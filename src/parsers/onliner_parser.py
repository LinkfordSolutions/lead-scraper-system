"""
Onliner.by parser - Services section
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from .base import BaseParser

logger = logging.getLogger(__name__)


class OnlinerParser(BaseParser):
    """Parser for Onliner.by services section"""

    # Category to Onliner services URL mappings
    CATEGORY_URLS = {
        'auto_service': 'https://baraholka.onliner.by/transportnye-uslugi',
        'handyman': 'https://baraholka.onliner.by/uslugi-mastera',
        'cleaning': 'https://baraholka.onliner.by/bytovye-uslugi',
        'moving': 'https://baraholka.onliner.by/transportnye-uslugi',
        'education': 'https://baraholka.onliner.by/obrazovanie-i-kursy',
        'fitness': 'https://baraholka.onliner.by/uslugi-sporta',
        'photo_video': 'https://baraholka.onliner.by/foto-video-uslugi',
        'legal': 'https://baraholka.onliner.by/yuridicheskie-uslugi',
        'psychology': 'https://baraholka.onliner.by/meditsina-i-zdorove',
        'tattoo': 'https://baraholka.onliner.by/uslugi-krasoty'
    }

    # Search keywords for each category
    CATEGORY_KEYWORDS = {
        'auto_service': ['автосервис', 'ремонт авто', 'шиномонтаж'],
        'handyman': ['мастер', 'ремонт квартир'],
        'cleaning': ['клининг', 'уборка'],
        'moving': ['грузоперевозки', 'переезд'],
        'education': ['репетитор', 'обучение'],
        'fitness': ['фитнес', 'тренер'],
        'photo_video': ['фотограф', 'видеосъемка'],
        'legal': ['юрист', 'адвокат'],
        'psychology': ['психолог'],
        'tattoo': ['тату', 'мастер тату']
    }

    def __init__(self):
        """Initialize Onliner parser"""
        super().__init__('onliner')
        self.base_url = 'https://baraholka.onliner.by'
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'ru-RU,ru;q=0.9'
            }
            self.session = aiohttp.ClientSession(headers=headers)
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
        Search ads by category on Onliner

        Args:
            category: Category name
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of company/service dictionaries
        """
        results = []

        # Get category URL
        category_url = self.CATEGORY_URLS.get(category)
        if not category_url:
            logger.warning(f"[Onliner] No URL mapping for category '{category}'")
            return results

        # Get search keywords
        keywords = self.CATEGORY_KEYWORDS.get(category, [])

        # Search each keyword
        for keyword in keywords:
            try:
                ads = await self._search_ads(category_url, keyword, city, limit // len(keywords))
                results.extend(ads)
                self.stats['total_found'] += len(ads)

                # Rate limiting
                await asyncio.sleep(2.0)

            except Exception as e:
                self.log_error(f"Search error for '{keyword}': {e}")

        logger.info(f"[Onliner] Found {len(results)} ads for category '{category}'")
        return results

    async def _search_ads(
        self,
        category_url: str,
        keyword: str,
        city: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search ads with keyword

        Args:
            category_url: Category page URL
            keyword: Search keyword
            city: City filter
            limit: Max results

        Returns:
            List of ads
        """
        ads = []
        session = await self._get_session()

        # Build search URL
        params = {
            'query': keyword
        }

        try:
            async with session.get(category_url, params=params, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find ad listings
                    ad_items = soup.select('.classified__item, .board__item')

                    for item in ad_items[:limit]:
                        try:
                            ad = self._parse_ad(item, keyword, city)
                            if ad:
                                ads.append(ad)
                                self.stats['successful'] += 1
                        except Exception as e:
                            self.log_error(f"Parse error: {e}")
                            self.stats['failed'] += 1

                else:
                    logger.warning(f"[Onliner] Page returned status {response.status}")

        except asyncio.TimeoutError:
            logger.warning(f"[Onliner] Request timeout")
        except Exception as e:
            logger.error(f"[Onliner] Request error: {e}")

        return ads

    def _parse_ad(self, item, keyword: str, city_filter: Optional[str]) -> Optional[Dict]:
        """
        Parse ad item

        Args:
            item: BeautifulSoup ad element
            keyword: Search keyword
            city_filter: City filter

        Returns:
            Normalized company/ad dictionary
        """
        try:
            # Get title
            title_elem = item.select_one('.classified__title, .board__title')
            if not title_elem:
                return None

            name = title_elem.get_text(strip=True)

            # Get link
            link_elem = item.select_one('a[href]')
            link = link_elem['href'] if link_elem else None
            if link and not link.startswith('http'):
                link = f"https://baraholka.onliner.by{link}"

            # Get description
            desc_elem = item.select_one('.classified__description, .board__description')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # Get location
            location_elem = item.select_one('.classified__location, .board__location')
            location = location_elem.get_text(strip=True) if location_elem else ''

            # Extract city from location
            city = self._extract_city(location)

            # Filter by city if specified
            if city_filter and city:
                if city_filter.lower() not in city.lower():
                    return None

            # Try to extract phone from description
            phone = self._extract_phone(description)

            # Build company dict
            company = {
                'name': name,
                'description': description,
                'address': location,
                'city': city,
                'phone': phone,
                'website': link,
                'category': keyword,
                'source': self.source_name,
                'raw_data': {
                    'title': name,
                    'description': description,
                    'location': location,
                    'url': link
                }
            }

            return company

        except Exception as e:
            logger.error(f"[Onliner] Parse error: {e}")
            return None

    def _extract_city(self, location: str) -> Optional[str]:
        """Extract city name from location string"""
        if not location:
            return None

        # Common Belarus cities
        cities = ['Минск', 'Гомель', 'Могилев', 'Витебск', 'Гродно', 'Брест']

        for city in cities:
            if city.lower() in location.lower():
                return city

        return location.split(',')[0] if ',' in location else location

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        if not text:
            return None

        # Belarus phone patterns
        patterns = [
            r'\+375\s?\d{2}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'80\d{2}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                return self.normalize_phone(phone)

        return None

    async def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get ad details by URL

        Args:
            company_id: Ad URL

        Returns:
            Ad details or None
        """
        if not company_id or not company_id.startswith('http'):
            return None

        session = await self._get_session()

        try:
            async with session.get(company_id, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extract additional details from ad page
                    # This can be enhanced based on actual page structure

                    return {
                        'url': company_id,
                        'source': self.source_name
                    }

        except Exception as e:
            logger.error(f"[Onliner] Get details error: {e}")

        return None
