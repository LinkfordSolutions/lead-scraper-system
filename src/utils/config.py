"""
Configuration loader and validator
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Application configuration"""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_BOT_USERNAME: str = os.getenv('TELEGRAM_BOT_USERNAME', '')
    BOT_PASSWORD: str = os.getenv('BOT_PASSWORD', '')

    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', 5432))
    DB_NAME: str = os.getenv('DB_NAME', 'lead_scraper_db')
    DB_USER: str = os.getenv('DB_USER', 'lead_scraper')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')

    # Scraping
    SCRAPING_SCHEDULE: str = os.getenv('SCRAPING_SCHEDULE', 'daily')
    SCRAPING_TIME: str = os.getenv('SCRAPING_TIME', '03:00')
    MAX_CONCURRENT_SCRAPERS: int = int(os.getenv('MAX_CONCURRENT_SCRAPERS', 3))

    # Geographic
    TARGET_COUNTRY: str = os.getenv('TARGET_COUNTRY', 'Belarus')
    TARGET_CITIES: str = os.getenv('TARGET_CITIES', 'all')

    # Proxy
    USE_PROXY: bool = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_LIST_URL: Optional[str] = os.getenv('PROXY_LIST_URL')
    PROXY_USERNAME: Optional[str] = os.getenv('PROXY_USERNAME')
    PROXY_PASSWORD: Optional[str] = os.getenv('PROXY_PASSWORD')

    # Rate Limiting
    YANDEX_MAPS_RATE_LIMIT: int = int(os.getenv('YANDEX_MAPS_RATE_LIMIT', 10))
    TWOGIS_RATE_LIMIT: int = int(os.getenv('TWOGIS_RATE_LIMIT', 15))
    INSTAGRAM_RATE_LIMIT: int = int(os.getenv('INSTAGRAM_RATE_LIMIT', 5))

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/scraper.log')

    # Data Export
    CSV_OUTPUT_DIR: str = os.getenv('CSV_OUTPUT_DIR', 'data')
    CSV_ENCODING: str = os.getenv('CSV_ENCODING', 'utf-8')

    # Niches
    ENABLED_NICHES: str = os.getenv('ENABLED_NICHES', 'all')

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")

        if not cls.BOT_PASSWORD:
            errors.append("BOT_PASSWORD is required")

        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")

        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    @classmethod
    def get_enabled_niches(cls) -> List[str]:
        """Get list of enabled niches"""
        if cls.ENABLED_NICHES == 'all':
            return [
                'auto_service',
                'handyman',
                'cleaning',
                'moving',
                'education',
                'fitness',
                'photo_video',
                'legal',
                'psychology',
                'tattoo'
            ]
        return [n.strip() for n in cls.ENABLED_NICHES.split(',')]

    @classmethod
    def print_config(cls):
        """Print current configuration (masking sensitive data)"""
        print("\n" + "="*50)
        print("CONFIGURATION")
        print("="*50)
        print(f"Bot Token: {'*' * 20}{cls.TELEGRAM_BOT_TOKEN[-10:]}")
        print(f"Bot Password: {'*' * len(cls.BOT_PASSWORD)}")
        print(f"Database: {cls.DB_NAME}@{cls.DB_HOST}:{cls.DB_PORT}")
        print(f"Scraping Schedule: {cls.SCRAPING_SCHEDULE} at {cls.SCRAPING_TIME}")
        print(f"Target: {cls.TARGET_COUNTRY} ({cls.TARGET_CITIES})")
        print(f"Enabled Niches: {', '.join(cls.get_enabled_niches())}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("="*50 + "\n")


# Export singleton instance
config = Config()
