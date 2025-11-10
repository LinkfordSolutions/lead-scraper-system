"""
2GIS API parser for Belarus
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from .base import BaseParser

logger = logging.getLogger(__name__)


class TwoGISParser(BaseParser):
    """Parser for 2GIS API"""

    # Belarus cities region IDs in 2GIS
    BELARUS_REGIONS = {
        'минск': '4504',  # Minsk
        'гомель': '4513',  # Gomel
        'могилев': '4518',  # Mogilev
        'витебск': '4521',  # Vitebsk
        'гродно': '4527',  # Grodno
        'брест': '4532',   # Brest
    }

    # Category mappings to 2GIS rubrics
    CATEGORY_RUBRICS = {
        'auto_service': ['автосервис', 'шиномонтаж', 'автомойка', 'детейлинг'],
        'handyman': ['мастер на час', 'сантехник', 'электрик', 'ремонт'],
        'cleaning': ['клининг', 'уборка', 'химчистка'],
        'moving': ['грузоперевозки', 'переезд', 'грузчики'],
        'education': ['репетитор', 'курсы', 'обучение', 'учебный центр'],
        'fitness': ['фитнес', 'спортзал', 'йога', 'танцы'],
        'photo_video': ['фотограф', 'фотостудия', 'видеосъемка'],
        'legal': ['юридические услуги', 'нотариус', 'адвокат'],
        'psychology': ['психолог', 'психотерапевт', 'коуч'],
        'tattoo': ['тату', 'татуировка', 'пирсинг', 'перманентный макияж']
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize 2GIS parser

        Args:
            api_key: 2GIS API key (optional, can work without for testing)
        """
        super().__init__('2gis')
        self.api_key = api_key or 'demo'  # Demo key for testing
        self.base_url = 'https://catalog.api.2gis.com/3.0'
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_by_category(
        self,
        category: str,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search companies by category in 2GIS

        Args:
            category: Category name (from CATEGORY_RUBRICS)
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of company dictionaries
        """
        results = []

        # Get search queries for category
        queries = self.CATEGORY_RUBRICS.get(category, [category])

        # Get region IDs to search
        regions = []
        if city:
            city_lower = city.lower()
            region_id = self.BELARUS_REGIONS.get(city_lower)
            if region_id:
                regions = [region_id]
        else:
            # Search all Belarus regions
            regions = list(self.BELARUS_REGIONS.values())

        # Search each query in each region
        for query in queries:
            for region_id in regions:
                try:
                    companies = await self._search_items(query, region_id, limit)
                    results.extend(companies)
                    self.stats['total_found'] += len(companies)

                    logger.info(
                        f"[2GIS] Found {len(companies)} companies "
                        f"for '{query}' in region {region_id}"
                    )

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    self.log_error(f"Search error for '{query}': {e}")
                    self.stats['failed'] += 1

        return results

    async def _search_items(
        self,
        query: str,
        region_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search items in 2GIS API

        Args:
            query: Search query
            region_id: Region ID
            limit: Maximum results

        Returns:
            List of companies
        """
        session = await self._get_session()
        url = f"{self.base_url}/items"

        params = {
            'q': query,
            'region_id': region_id,
            'page_size': min(limit, 50),  # Max 50 per request
            'key': self.api_key,
            'fields': 'items.reviews,items.point,items.contact_groups,items.schedule'
        }

        companies = []

        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()

                    if 'result' in data and 'items' in data['result']:
                        for item in data['result']['items']:
                            company = self._parse_item(item)
                            if company:
                                companies.append(company)
                                self.stats['successful'] += 1
                else:
                    logger.error(f"[2GIS] API error: {response.status}")
                    self.stats['failed'] += 1

        except asyncio.TimeoutError:
            logger.error(f"[2GIS] Timeout for query: {query}")
            self.stats['failed'] += 1
        except Exception as e:
            logger.error(f"[2GIS] Error: {e}")
            self.stats['failed'] += 1

        return companies

    def _parse_item(self, item: Dict) -> Optional[Dict]:
        """
        Parse 2GIS item to company dictionary

        Args:
            item: Raw item from API

        Returns:
            Normalized company dict or None
        """
        try:
            # Extract basic info
            company = {
                'name': item.get('name'),
                'source': '2gis',
                'source_id': item.get('id'),
                'source_url': item.get('link'),
                'raw_data': item
            }

            # Address
            if 'address' in item:
                address_data = item['address']
                company['address'] = address_data.get('name')
                if 'components' in address_data:
                    for comp in address_data['components']:
                        if comp.get('type') == 'city':
                            company['city'] = comp.get('name')
                        elif comp.get('type') == 'district':
                            company['district'] = comp.get('name')

            # Coordinates
            if 'point' in item:
                point = item['point']
                company['latitude'] = point.get('lat')
                company['longitude'] = point.get('lon')

            # Contacts
            if 'contact_groups' in item:
                for group in item['contact_groups']:
                    for contact in group.get('contacts', []):
                        contact_type = contact.get('type')
                        contact_value = contact.get('value') or contact.get('text')

                        if contact_type == 'phone':
                            if not company.get('phone'):
                                company['phone'] = self.normalize_phone(contact_value)
                        elif contact_type == 'email':
                            company['email'] = contact_value
                        elif contact_type == 'website':
                            company['website'] = contact_value

            # Reviews and rating
            if 'reviews' in item:
                reviews = item['reviews']
                company['rating'] = reviews.get('rating')
                company['reviews_count'] = reviews.get('total')

            # Check if city is in Belarus
            if company.get('city') and self.is_belarus_city(company['city']):
                return company

            return None

        except Exception as e:
            self.log_error(f"Parse error: {e}", item.get('id'))
            return None

    async def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get detailed information about a company

        Args:
            company_id: Company ID in 2GIS

        Returns:
            Company details or None
        """
        session = await self._get_session()
        url = f"{self.base_url}/items/byid"

        params = {
            'id': company_id,
            'key': self.api_key,
            'fields': 'items.reviews,items.point,items.contact_groups,items.schedule,items.rubrics'
        }

        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()

                    if 'result' in data and 'items' in data['result']:
                        items = data['result']['items']
                        if items:
                            return self._parse_item(items[0])

        except Exception as e:
            self.log_error(f"Details error: {e}", company_id)

        return None


async def test_parser():
    """Test 2GIS parser"""
    parser = TwoGISParser()

    try:
        print("Testing 2GIS parser...")
        print("Searching auto_service in Minsk...")

        results = await parser.search_by_category('auto_service', 'минск', limit=5)

        print(f"\nFound {len(results)} companies")
        for company in results[:3]:
            print(f"\n- {company['name']}")
            print(f"  Address: {company.get('address')}")
            print(f"  Phone: {company.get('phone')}")
            print(f"  Rating: {company.get('rating')}")

        print(f"\nStats: {parser.get_stats()}")

    finally:
        await parser.close()


if __name__ == '__main__':
    asyncio.run(test_parser())
