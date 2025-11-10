"""
Test script for all parsers
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from src.parsers.yandex_parser import YandexMapsParser
from src.parsers.egr_parser import EGRParser
from src.parsers.onliner_parser import OnlinerParser
from src.parsers.deal_parser import DealParser
from src.parsers.instagram_parser import InstagramParser
from src.parsers.twogis_parser import TwoGISParser

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def test_parser(parser, parser_name: str, category: str):
    """Test a single parser"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {parser_name}")
    logger.info(f"{'='*60}")

    try:
        # Search
        results = await parser.search_by_category(
            category=category,
            city='минск',
            limit=5
        )

        logger.info(f"✅ {parser_name}: Found {len(results)} results")

        # Show first result
        if results:
            first = results[0]
            logger.info(f"\nSample result:")
            logger.info(f"  Name: {first.get('name', 'N/A')}")
            logger.info(f"  City: {first.get('city', 'N/A')}")
            logger.info(f"  Phone: {first.get('phone', 'N/A')}")
            logger.info(f"  Address: {first.get('address', 'N/A')[:50] if first.get('address') else 'N/A'}")

        # Get stats
        stats = parser.get_stats()
        logger.info(f"\nStats:")
        logger.info(f"  Total found: {stats['total_found']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")

        # Close parser
        await parser.close()

        return True

    except Exception as e:
        logger.error(f"❌ {parser_name} failed: {e}", exc_info=True)
        return False


async def main():
    """Run all parser tests"""
    logger.info("="*60)
    logger.info("PARSER TESTING SUITE")
    logger.info("="*60)

    test_category = 'auto_service'
    results = {}

    # Test 2GIS Parser
    parser = TwoGISParser(api_key='demo')
    results['2GIS'] = await test_parser(parser, '2GIS', test_category)
    await asyncio.sleep(2)

    # Test Yandex Maps Parser
    parser = YandexMapsParser(api_key='demo')
    results['Yandex Maps'] = await test_parser(parser, 'Yandex Maps', test_category)
    await asyncio.sleep(2)

    # Test EGR Parser
    parser = EGRParser()
    results['EGR'] = await test_parser(parser, 'EGR.gov.by', test_category)
    await asyncio.sleep(2)

    # Test Onliner Parser
    parser = OnlinerParser()
    results['Onliner'] = await test_parser(parser, 'Onliner.by', test_category)
    await asyncio.sleep(2)

    # Test Deal Parser
    parser = DealParser()
    results['Deal'] = await test_parser(parser, 'Deal.by', test_category)
    await asyncio.sleep(2)

    # Test Instagram Parser
    parser = InstagramParser()
    results['Instagram'] = await test_parser(parser, 'Instagram', test_category)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")

    for parser_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{parser_name:20} {status}")

    passed = sum(1 for s in results.values() if s)
    total = len(results)

    logger.info(f"\nTotal: {passed}/{total} parsers passed")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
