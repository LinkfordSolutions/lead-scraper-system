"""
Quick test - verify all parsers can be imported and initialized
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("PARSER IMPORT TEST")
print("="*60)

tests_passed = []
tests_failed = []

# Test 2GIS Parser
try:
    from src.parsers.twogis_parser import TwoGISParser
    parser = TwoGISParser(api_key='demo')
    assert parser.source_name == '2gis'
    tests_passed.append('2GIS Parser')
    print("✅ 2GIS Parser - OK")
except Exception as e:
    tests_failed.append(f'2GIS Parser: {e}')
    print(f"❌ 2GIS Parser - FAILED: {e}")

# Test Yandex Maps Parser
try:
    from src.parsers.yandex_parser import YandexMapsParser
    parser = YandexMapsParser(api_key='demo')
    assert parser.source_name == 'yandex_maps'
    tests_passed.append('Yandex Maps Parser')
    print("✅ Yandex Maps Parser - OK")
except Exception as e:
    tests_failed.append(f'Yandex Maps Parser: {e}')
    print(f"❌ Yandex Maps Parser - FAILED: {e}")

# Test EGR Parser
try:
    from src.parsers.egr_parser import EGRParser
    parser = EGRParser()
    assert parser.source_name == 'egr'
    tests_passed.append('EGR Parser')
    print("✅ EGR Parser - OK")
except Exception as e:
    tests_failed.append(f'EGR Parser: {e}')
    print(f"❌ EGR Parser - FAILED: {e}")

# Test Onliner Parser
try:
    from src.parsers.onliner_parser import OnlinerParser
    parser = OnlinerParser()
    assert parser.source_name == 'onliner'
    tests_passed.append('Onliner Parser')
    print("✅ Onliner Parser - OK")
except Exception as e:
    tests_failed.append(f'Onliner Parser: {e}')
    print(f"❌ Onliner Parser - FAILED: {e}")

# Test Deal Parser
try:
    from src.parsers.deal_parser import DealParser
    parser = DealParser()
    assert parser.source_name == 'deal'
    tests_passed.append('Deal Parser')
    print("✅ Deal Parser - OK")
except Exception as e:
    tests_failed.append(f'Deal Parser: {e}')
    print(f"❌ Deal Parser - FAILED: {e}")

# Test Instagram Parser
try:
    from src.parsers.instagram_parser import InstagramParser
    parser = InstagramParser()
    assert parser.source_name == 'instagram'
    tests_passed.append('Instagram Parser')
    print("✅ Instagram Parser - OK")
except Exception as e:
    tests_failed.append(f'Instagram Parser: {e}')
    print(f"❌ Instagram Parser - FAILED: {e}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"✅ Passed: {len(tests_passed)}")
print(f"❌ Failed: {len(tests_failed)}")

if tests_failed:
    print("\nFailed tests:")
    for fail in tests_failed:
        print(f"  - {fail}")

print("="*60)

# Exit with appropriate code
sys.exit(0 if len(tests_failed) == 0 else 1)
