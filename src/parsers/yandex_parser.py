"""
Yandex Maps API parser for Belarus
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from .base import BaseParser

logger = logging.getLogger(__name__)


class YandexMapsParser(BaseParser):
    """Parser for Yandex Maps API"""

    # Belarus cities coordinates (lat, lon)
    BELARUS_CITIES = {
        'минск': (53.9006, 27.5590),
        'гомель': (52.4345, 30.9754),
        'могилев': (53.9007, 30.3313),
        'витебск': (55.1904, 30.2049),
        'гродно': (53.6884, 23.8258),
        'брест': (52.0976, 23.7340),
        'бобруйск': (53.1484, 29.2214),
        'барановичи': (53.1327, 26.0139),
        'борисов': (54.2274, 28.5051),
        'пинск': (52.1229, 26.0951),
    }

    # Category mappings to Yandex search terms
    CATEGORY_KEYWORDS = {
        'auto_service': ['автосервис', 'шиномонтаж', 'автомойка', 'детейлинг авто'],
        'handyman': ['мастер на час', 'мастер на дом', 'мелкий ремонт'],
        'cleaning': ['клининг', 'клининговые услуги', 'уборка квартир'],
        'moving': ['грузоперевозки', 'переезд квартирный', 'грузчики'],
        'education': ['репетитор', 'репетиторские услуги', 'курсы обучения'],
        'fitness': ['фитнес клуб', 'тренажерный зал', 'йога студия'],
        'photo_video': ['фотограф', 'фотостудия', 'видеосъемка'],
        'legal': ['юридические услуги', 'юридическая консультация', 'адвокат'],
        'psychology': ['психолог', 'психологическая помощь', 'психотерапевт'],
        'tattoo': ['тату салон', 'татуировка', 'тату студия']
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Yandex Maps parser

        Args:
            api_key: Yandex Maps API key
        """
        super().__init__('yandex_maps')
        self.api_key = api_key or 'demo'  # Demo key for testing
        self.base_url = 'https://search-maps.yandex.ru/v1/'
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
        Search companies by category in Yandex Maps

        Args:
            category: Category name (from CATEGORY_KEYWORDS)
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of company dictionaries
        """
        results = []

        # Get search keywords for category
        keywords = self.CATEGORY_KEYWORDS.get(category, [category])

        # Get cities to search
        cities = {}
        if city:
            city_lower = city.lower()
            coords = self.BELARUS_CITIES.get(city_lower)
            if coords:
                cities[city_lower] = coords
        else:
            # Search all Belarus cities
            cities = self.BELARUS_CITIES

        # Search each keyword in each city
        for keyword in keywords:
            for city_name, coords in cities.items():
                try:
                    companies = await self._search_organizations(
                        keyword,
                        coords,
                        city_name,
                        limit
                    )
                    results.extend(companies)
                    self.stats['total_found'] += len(companies)

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    self.log_error(f"Search error for '{keyword}' in {city_name}: {e}")

        logger.info(f"[Yandex Maps] Found {len(results)} companies for category '{category}'")
        return results

    async def _search_organizations(
        self,
        query: str,
        coords: tuple,
        city_name: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search organizations via Yandex Maps API

        Args:
            query: Search query
            coords: (latitude, longitude) tuple
            city_name: City name for filtering
            limit: Maximum results

        Returns:
            List of company dictionaries
        """
        companies = []
        session = await self._get_session()

        # Yandex Maps Search API parameters
        params = {
            'apikey': self.api_key,
            'text': query,
            'll': f"{coords[1]},{coords[0]}",  # lon,lat format
            'spn': '0.5,0.5',  # Search area span
            'lang': 'ru_RU',
            'type': 'biz',  # Business search
            'results': min(limit, 50)  # Max 50 per request
        }

        try:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse response
                    features = data.get('features', [])

                    for feature in features:
                        try:
                            company = self._parse_company(feature, city_name, query)
                            if company:
                                companies.append(company)
                                self.stats['successful'] += 1
                        except Exception as e:
                            self.log_error(f"Parse error: {e}")
                            self.stats['failed'] += 1

                elif response.status == 403:
                    logger.warning("[Yandex Maps] API key invalid or quota exceeded")
                else:
                    logger.warning(f"[Yandex Maps] API returned status {response.status}")

        except Exception as e:
            logger.error(f"[Yandex Maps] Request error: {e}")

        return companies

    def _parse_company(self, feature: Dict, city: str, category_query: str) -> Optional[Dict]:
        """
        Parse company from Yandex Maps feature

        Args:
            feature: Feature object from API
            city: City name
            category_query: Original search query

        Returns:
            Normalized company dictionary
        """
        try:
            properties = feature.get('properties', {})
            company_meta = properties.get('CompanyMetaData', {})

            # Get basic info
            name = properties.get('name', '').strip()
            if not name:
                return None

            # Get address
            address = company_meta.get('address', '')

            # Get coordinates
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])

            # Get contact info
            phones = []
            phone_data = company_meta.get('Phones', [])
            for phone_item in phone_data:
                formatted = phone_item.get('formatted')
                if formatted:
                    normalized = self.normalize_phone(formatted)
                    if normalized:
                        phones.append(normalized)

            # Get website
            website = company_meta.get('url')

            # Get categories
            categories = company_meta.get('Categories', [])
            category_names = [cat.get('name', '') for cat in categories]

            # Build company dict
            company = {
                'name': name,
                'address': address,
                'city': city,
                'phone': phones[0] if phones else None,
                'phones': phones,
                'website': website,
                'category': category_query,
                'categories': category_names,
                'latitude': coordinates[1] if len(coordinates) > 1 else None,
                'longitude': coordinates[0] if len(coordinates) > 0 else None,
                'source': self.source_name,
                'raw_data': properties
            }

            # Extract social links if available
            socials = self.extract_social_links(properties)
            company.update(socials)

            return company

        except Exception as e:
            logger.error(f"[Yandex Maps] Parse error: {e}")
            return None

    async def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get detailed information about a company

        Note: Yandex Maps API doesn't have a direct "get by ID" endpoint,
        so we return None. Details are already included in search results.

        Args:
            company_id: Company ID (not used for Yandex)

        Returns:
            None (details already in search results)
        """
        return None
