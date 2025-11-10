"""
Telegram Bot main application
"""
import logging
import sys
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.config import config
from src.bot.handlers import (
    start_command,
    auth_command,
    get_leads_command,
    status_command,
    help_command,
    error_handler
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class LeadScraperBot:
    """Main bot application"""

    def __init__(self):
        """Initialize bot"""
        self.token = config.TELEGRAM_BOT_TOKEN
        self.application = None

    def setup_handlers(self):
        """Setup command handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("auth", auth_command))
        self.application.add_handler(CommandHandler("get_leads", get_leads_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("help", help_command))

        # Error handler
        self.application.add_error_handler(error_handler)

        logger.info("✅ Bot handlers configured")

    async def post_init(self, application: Application):
        """Post initialization"""
        bot_info = await application.bot.get_me()
        logger.info(f"🤖 Bot started: @{bot_info.username}")
        logger.info(f"📝 Bot name: {bot_info.first_name}")
        logger.info(f"🆔 Bot ID: {bot_info.id}")

    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting Lead Scraper Bot...")

        # Validate config
        if not config.validate():
            logger.error("❌ Configuration validation failed")
            sys.exit(1)

        # Create application
        self.application = Application.builder().token(self.token).build()

        # Setup handlers
        self.setup_handlers()

        # Add post init callback
        self.application.post_init = self.post_init

        # Start polling
        logger.info("🔄 Starting polling...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


def main():
    """Main entry point"""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Create and run bot
    bot = LeadScraperBot()
    bot.run()


if __name__ == '__main__':
    main()
