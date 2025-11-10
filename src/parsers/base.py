"""
Base parser class for all scrapers
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base class for all parsers"""

    def __init__(self, source_name: str):
        """
        Initialize parser

        Args:
            source_name: Name of the data source
        """
        self.source_name = source_name
        self.stats = {
            'total_found': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

    @abstractmethod
    async def search_by_category(
        self,
        category: str,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search companies by category

        Args:
            category: Category name
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of company dictionaries
        """
        pass

    @abstractmethod
    async def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get detailed information about a company

        Args:
            company_id: Company ID from source

        Returns:
            Company details dictionary or None
        """
        pass

    def normalize_phone(self, phone: str) -> Optional[str]:
        """
        Normalize phone number to +375 format

        Args:
            phone: Raw phone number

        Returns:
            Normalized phone or None
        """
        if not phone:
            return None

        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))

        # Belarus formats
        if digits.startswith('375'):
            return f"+{digits}"
        elif digits.startswith('80'):
            return f"+375{digits[2:]}"
        elif len(digits) == 9:
            return f"+375{digits}"

        return phone

    def extract_social_links(self, raw_data: Dict) -> Dict[str, Optional[str]]:
        """
        Extract social media links from raw data

        Args:
            raw_data: Raw company data

        Returns:
            Dictionary with social links
        """
        socials = {
            'instagram': None,
            'facebook': None,
            'vk': None,
            'telegram': None
        }

        # Try to find social links in various fields
        for key, value in raw_data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                if 'instagram.com' in value_lower or '@' in value_lower:
                    socials['instagram'] = value
                elif 'facebook.com' in value_lower or 'fb.com' in value_lower:
                    socials['facebook'] = value
                elif 'vk.com' in value_lower:
                    socials['vk'] = value
                elif 't.me' in value_lower or 'telegram' in value_lower:
                    socials['telegram'] = value

        return socials

    def is_belarus_city(self, city: str) -> bool:
        """
        Check if city is in Belarus

        Args:
            city: City name

        Returns:
            True if city is in Belarus
        """
        belarus_cities = [
            'минск', 'гомель', 'могилев', 'витебск', 'гродно', 'брест',
            'бобруйск', 'барановичи', 'борисов', 'пинск', 'орша', 'мозырь',
            'солигорск', 'новополоцк', 'лида', 'молодечно', 'полоцк', 'жлобин',
            'minsk', 'gomel', 'mogilev', 'vitebsk', 'grodno', 'brest'
        ]

        if not city:
            return False

        city_lower = city.lower()
        return any(belarus_city in city_lower for belarus_city in belarus_cities)

    def get_stats(self) -> Dict:
        """
        Get parsing statistics

        Returns:
            Statistics dictionary
        """
        return {
            'source': self.source_name,
            'total_found': self.stats['total_found'],
            'successful': self.stats['successful'],
            'failed': self.stats['failed'],
            'error_count': len(self.stats['errors']),
            'success_rate': (
                self.stats['successful'] / self.stats['total_found'] * 100
                if self.stats['total_found'] > 0 else 0
            )
        }

    def log_error(self, error: str, company_id: Optional[str] = None):
        """
        Log parsing error

        Args:
            error: Error message
            company_id: Company ID (optional)
        """
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(error),
            'company_id': company_id
        }
        self.stats['errors'].append(error_info)
        logger.error(f"[{self.source_name}] {error}", extra={'company_id': company_id})
