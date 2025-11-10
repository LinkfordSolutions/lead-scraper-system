"""
Deal.by parser - Classifieds website
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from .base import BaseParser

logger = logging.getLogger(__name__)


class DealParser(BaseParser):
    """Parser for Deal.by classifieds"""

    # Category to Deal.by section IDs
    CATEGORY_SECTIONS = {
        'auto_service': 'uslugi/avto',
        'handyman': 'uslugi/master-na-chas',
        'cleaning': 'uslugi/bytovye',
        'moving': 'uslugi/gruzoperevozki',
        'education': 'uslugi/obrazovanie',
        'fitness': 'uslugi/sport-fitnes',
        'photo_video': 'uslugi/foto-video',
        'legal': 'uslugi/yuridicheskie',
        'psychology': 'uslugi/meditsina-zdorove',
        'tattoo': 'uslugi/krasota'
    }

    # Belarus regions for Deal.by
    REGIONS = {
        'минск': 'minsk',
        'гомель': 'gomel',
        'могилев': 'mogilev',
        'витебск': 'vitebsk',
        'гродно': 'grodno',
        'брест': 'brest'
    }

    def __init__(self):
        """Initialize Deal parser"""
        super().__init__('deal')
        self.base_url = 'https://deal.by'
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
        Search ads by category on Deal.by

        Args:
            category: Category name
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of company/service dictionaries
        """
        results = []

        # Get category section
        section = self.CATEGORY_SECTIONS.get(category)
        if not section:
            logger.warning(f"[Deal.by] No section mapping for category '{category}'")
            return results

        # Get regions to search
        regions = []
        if city:
            city_lower = city.lower()
            region = self.REGIONS.get(city_lower)
            if region:
                regions = [region]
        else:
            # Search all regions
            regions = list(self.REGIONS.values())

        # Search each region
        for region in regions:
            try:
                ads = await self._search_region(section, region, limit // len(regions))
                results.extend(ads)
                self.stats['total_found'] += len(ads)

                # Rate limiting
                await asyncio.sleep(2.0)

            except Exception as e:
                self.log_error(f"Search error for region '{region}': {e}")

        logger.info(f"[Deal.by] Found {len(results)} ads for category '{category}'")
        return results

    async def _search_region(
        self,
        section: str,
        region: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search ads in specific region

        Args:
            section: Category section path
            region: Region slug
            limit: Max results

        Returns:
            List of ads
        """
        ads = []
        session = await self._get_session()

        # Build URL
        url = f"{self.base_url}/{region}/{section}"

        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find ad listings (adjust selectors based on actual site structure)
                    ad_items = soup.select('.listing__item, .classified, .advert-item')

                    for item in ad_items[:limit]:
                        try:
                            ad = self._parse_ad(item, region)
                            if ad:
                                ads.append(ad)
                                self.stats['successful'] += 1
                        except Exception as e:
                            self.log_error(f"Parse error: {e}")
                            self.stats['failed'] += 1

                else:
                    logger.warning(f"[Deal.by] Page returned status {response.status}")

        except asyncio.TimeoutError:
            logger.warning(f"[Deal.by] Request timeout for {url}")
        except Exception as e:
            logger.error(f"[Deal.by] Request error: {e}")

        return ads

    def _parse_ad(self, item, region: str) -> Optional[Dict]:
        """
        Parse ad item

        Args:
            item: BeautifulSoup ad element
            region: Region slug

        Returns:
            Normalized company/ad dictionary
        """
        try:
            # Get title (adjust selectors based on actual site)
            title_elem = item.select_one('.listing__title, h3, .title')
            if not title_elem:
                return None

            name = title_elem.get_text(strip=True)

            # Get link
            link_elem = item.select_one('a[href]')
            link = link_elem['href'] if link_elem else None
            if link and not link.startswith('http'):
                link = f"{self.base_url}{link}"

            # Get description
            desc_elem = item.select_one('.listing__text, .description, .text')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # Get price (if available)
            price_elem = item.select_one('.listing__price, .price')
            price = price_elem.get_text(strip=True) if price_elem else None

            # Get location/city
            city = self._region_to_city(region)

            # Try to extract phone
            phone = self._extract_phone(description)

            # Build company dict
            company = {
                'name': name,
                'description': description,
                'city': city,
                'phone': phone,
                'website': link,
                'price': price,
                'source': self.source_name,
                'raw_data': {
                    'title': name,
                    'description': description,
                    'region': region,
                    'url': link,
                    'price': price
                }
            }

            return company

        except Exception as e:
            logger.error(f"[Deal.by] Parse error: {e}")
            return None

    def _region_to_city(self, region: str) -> str:
        """Convert region slug to city name"""
        region_map = {
            'minsk': 'Минск',
            'gomel': 'Гомель',
            'mogilev': 'Могилев',
            'vitebsk': 'Витебск',
            'grodno': 'Гродно',
            'brest': 'Брест'
        }
        return region_map.get(region, region)

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        if not text:
            return None

        # Belarus phone patterns
        patterns = [
            r'\+375\s?\d{2}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'80\d{2}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\d{2,3}[-\s]?\d{2}[-\s]?\d{2}'
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

                    # Extract phone from ad page
                    phone_elem = soup.select_one('.phone, .contact-phone, [data-phone]')
                    phone = None
                    if phone_elem:
                        phone_text = phone_elem.get('data-phone') or phone_elem.get_text()
                        phone = self.normalize_phone(phone_text)

                    return {
                        'url': company_id,
                        'phone': phone,
                        'source': self.source_name
                    }

        except Exception as e:
            logger.error(f"[Deal.by] Get details error: {e}")

        return None
