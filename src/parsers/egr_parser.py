"""
EGR.gov.by parser - Belarus State Register
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from .base import BaseParser

logger = logging.getLogger(__name__)


class EGRParser(BaseParser):
    """Parser for Belarus State Register (egr.gov.by)"""

    # Category to ОКЭД (OKED) code mappings
    # These are economic activity codes used in Belarus
    CATEGORY_OKED = {
        'auto_service': ['45.20', '45.3', '45.4'],  # Maintenance and repair of motor vehicles
        'handyman': ['43.2', '43.3', '43.9'],  # Specialized construction activities
        'cleaning': ['81.2', '81.29'],  # Cleaning activities
        'moving': ['49.4', '52.29'],  # Freight transport
        'education': ['85.5', '85.59'],  # Other education
        'fitness': ['93.1', '93.13'],  # Fitness facilities
        'photo_video': ['74.20', '59.11'],  # Photographic activities, motion picture
        'legal': ['69.1', '69.10'],  # Legal activities
        'psychology': ['86.90'],  # Other human health activities
        'tattoo': ['96.02', '96.09']  # Hairdressing and other beauty treatment
    }

    # Category keywords for text search (fallback)
    CATEGORY_KEYWORDS = {
        'auto_service': ['автосервис', 'авторемонт', 'шиномонтаж'],
        'handyman': ['мастер', 'ремонт', 'сантехник'],
        'cleaning': ['клининг', 'уборка'],
        'moving': ['грузоперевозк', 'перевозк'],
        'education': ['репетитор', 'обучение', 'курсы'],
        'fitness': ['фитнес', 'спорт'],
        'photo_video': ['фото', 'видео'],
        'legal': ['юридическ', 'адвокат'],
        'psychology': ['психолог'],
        'tattoo': ['тату', 'салон красоты']
    }

    def __init__(self):
        """Initialize EGR parser"""
        super().__init__('egr')
        self.base_url = 'https://egr.gov.by/api/v2'
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
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
        Search companies by category in EGR

        Args:
            category: Category name
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of company dictionaries
        """
        results = []

        # Get OKED codes for category
        oked_codes = self.CATEGORY_OKED.get(category, [])

        # Search by OKED codes
        for oked in oked_codes:
            try:
                companies = await self._search_by_oked(oked, city, limit // len(oked_codes))
                results.extend(companies)
                self.stats['total_found'] += len(companies)

                # Rate limiting
                await asyncio.sleep(1.0)

            except Exception as e:
                self.log_error(f"Search error for OKED {oked}: {e}")

        # Fallback: search by keywords if OKED search didn't return enough results
        if len(results) < limit // 2:
            keywords = self.CATEGORY_KEYWORDS.get(category, [])
            for keyword in keywords:
                try:
                    companies = await self._search_by_keyword(keyword, city, limit // len(keywords))
                    results.extend(companies)
                    self.stats['total_found'] += len(companies)

                    # Rate limiting
                    await asyncio.sleep(1.0)

                except Exception as e:
                    self.log_error(f"Search error for keyword '{keyword}': {e}")

        logger.info(f"[EGR] Found {len(results)} companies for category '{category}'")
        return results

    async def _search_by_oked(
        self,
        oked: str,
        city: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search by OKED code

        Args:
            oked: OKED economic activity code
            city: City name filter
            limit: Max results

        Returns:
            List of companies
        """
        companies = []
        session = await self._get_session()

        # EGR API search parameters
        params = {
            'oked': oked,
            'limit': min(limit, 100),
            'offset': 0
        }

        if city:
            params['region'] = city

        try:
            url = f"{self.base_url}/registry/search"
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse results
                    items = data.get('data', {}).get('items', [])

                    for item in items:
                        try:
                            company = self._parse_company(item)
                            if company:
                                companies.append(company)
                                self.stats['successful'] += 1
                        except Exception as e:
                            self.log_error(f"Parse error: {e}")
                            self.stats['failed'] += 1

                else:
                    logger.warning(f"[EGR] API returned status {response.status}")

        except asyncio.TimeoutError:
            logger.warning(f"[EGR] Request timeout for OKED {oked}")
        except Exception as e:
            logger.error(f"[EGR] Request error: {e}")

        return companies

    async def _search_by_keyword(
        self,
        keyword: str,
        city: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search by keyword (company name)

        Args:
            keyword: Search keyword
            city: City filter
            limit: Max results

        Returns:
            List of companies
        """
        companies = []
        session = await self._get_session()

        params = {
            'name': keyword,
            'limit': min(limit, 100),
            'offset': 0
        }

        if city:
            params['region'] = city

        try:
            url = f"{self.base_url}/registry/search"
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('data', {}).get('items', [])

                    for item in items:
                        try:
                            company = self._parse_company(item)
                            if company:
                                companies.append(company)
                                self.stats['successful'] += 1
                        except Exception as e:
                            self.log_error(f"Parse error: {e}")
                            self.stats['failed'] += 1

        except asyncio.TimeoutError:
            logger.warning(f"[EGR] Request timeout for keyword '{keyword}'")
        except Exception as e:
            logger.error(f"[EGR] Request error: {e}")

        return companies

    def _parse_company(self, item: Dict) -> Optional[Dict]:
        """
        Parse company from EGR data

        Args:
            item: Company item from API

        Returns:
            Normalized company dictionary
        """
        try:
            # Get basic info
            name = item.get('vnaim', '') or item.get('naimk', '')
            if not name:
                return None

            name = name.strip()

            # Get registration number (УНП)
            unp = item.get('vnp', '') or item.get('ngrn', '')

            # Get address
            address = item.get('address', '') or item.get('vpadres', '')

            # Get region/city
            region = item.get('voblast', '') or item.get('region', '')

            # Get legal form
            legal_form = item.get('vorgf', '')

            # Get registration date
            reg_date = item.get('dlikv', '') or item.get('dreg', '')

            # Get OKED codes
            oked = item.get('vidsDeятельности', [])
            if isinstance(oked, str):
                oked = [oked]

            # Build company dict
            company = {
                'name': name,
                'address': address,
                'city': region,
                'unp': unp,  # УНП - unique taxpayer number
                'legal_form': legal_form,
                'registration_date': reg_date,
                'oked_codes': oked,
                'phone': None,  # EGR doesn't provide phones
                'website': None,
                'source': self.source_name,
                'raw_data': item
            }

            return company

        except Exception as e:
            logger.error(f"[EGR] Parse error: {e}")
            return None

    async def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get detailed information about a company by УНП

        Args:
            company_id: УНП (unique taxpayer number)

        Returns:
            Company details or None
        """
        session = await self._get_session()

        try:
            url = f"{self.base_url}/registry/{company_id}"
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    company_data = data.get('data', {})
                    return self._parse_company(company_data)

        except Exception as e:
            logger.error(f"[EGR] Get details error: {e}")

        return None
