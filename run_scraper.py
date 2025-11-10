"""
Manual scraper runner - for testing and manual scraping
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from src.parsers.parser_manager import parser_manager
from src.parsers.twogis_parser import TwoGISParser
from src.utils.config import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MockParser:
    """Mock parser for testing without real API calls"""

    def __init__(self):
        self.source_name = 'mock_test'

    async def search_by_category(self, category: str, city=None, limit=100):
        """Generate mock companies for category"""
        await asyncio.sleep(0.5)  # Simulate API delay

        mock_companies = [
            {
                'name': f'Тестовая компания {category} №1',
                'address': f'ул. Тестовая 1, Минск',
                'city': 'Минск',
                'phone': '+375291234567',
                'email': f'test1@{category}.by',
                'website': f'https://{category}1.by',
                'instagram': f'@{category}_1',
                'rating': 4.5,
                'reviews_count': 50,
                'latitude': 53.9006,
                'longitude': 27.5590,
                'source': 'mock_test',
                'source_id': f'mock_{category}_1'
            },
            {
                'name': f'Компания "{category.capitalize()}" №2',
                'address': f'пр. Независимости 50, Минск',
                'city': 'Минск',
                'phone': '+375297654321',
                'rating': 4.8,
                'reviews_count': 120,
                'latitude': 53.9168,
                'longitude': 27.5909,
                'source': 'mock_test',
                'source_id': f'mock_{category}_2'
            }
        ]

        return mock_companies

    async def close(self):
        """Mock close"""
        pass


async def run_scraping(use_mock: bool = False):
    """
    Run scraping process

    Args:
        use_mock: Use mock parser instead of real APIs
    """
    logger.info("="*60)
    logger.info("Starting Lead Scraper")
    logger.info("="*60)

    # Register parsers
    if use_mock:
        logger.info("Using MOCK parser for testing")
        mock_parser = MockParser()
        parser_manager.register_parser(mock_parser)
    else:
        logger.info("Using real 2GIS parser")
        twogis = TwoGISParser()
        parser_manager.register_parser(twogis)

    # Get categories to scrape
    categories = config.get_enabled_niches()
    logger.info(f"Categories to scrape: {', '.join(categories)}")

    try:
        # Run scraping
        await parser_manager.run_all_parsers(categories)

        logger.info("="*60)
        logger.info("Scraping completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)

    finally:
        # Cleanup
        for parser in parser_manager.parsers:
            if hasattr(parser, 'close'):
                await parser.close()


async def main():
    """Main entry point"""
    # Check arguments
    use_mock = '--mock' in sys.argv or '-m' in sys.argv

    if use_mock:
        print("\n🧪 Running with MOCK data for testing\n")
    else:
        print("\n🌐 Running with REAL APIs\n")

    await run_scraping(use_mock)


if __name__ == '__main__':
    asyncio.run(main())
