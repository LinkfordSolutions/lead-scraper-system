"""
Lead Scraper System - Main Entry Point
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import config
from src.database.db import init_database


def main():
    """Main application entry point"""
    print("🚀 Lead Scraper System")
    print("=" * 50)

    # Validate configuration
    if not config.validate():
        print("\n❌ Configuration validation failed!")
        sys.exit(1)

    # Print configuration
    config.print_config()

    # Initialize database
    print("Initializing database...")
    try:
        init_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

    print("\n✅ System initialized successfully!")
    print("\nNext steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Start the Telegram bot")
    print("  3. Configure scrapers")
    print("  4. Run first scraping session")


if __name__ == '__main__':
    main()
