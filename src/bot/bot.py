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
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.config import config
from src.bot.handlers import (
    start_command,
    button_auth_start,
    receive_password,
    button_info,
    button_cancel,
    handle_text_message,
    error_handler,
    WAITING_PASSWORD
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

        # Authorization conversation handler
        auth_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(button_auth_start, pattern="^auth_start$")],
            states={
                WAITING_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)
                ],
            },
            fallbacks=[
                CallbackQueryHandler(button_cancel, pattern="^cancel$"),
                CommandHandler("start", start_command)
            ],
        )

        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))

        # Conversation handler for auth
        self.application.add_handler(auth_conv_handler)

        # Callback query handlers (inline buttons)
        self.application.add_handler(CallbackQueryHandler(button_info, pattern="^info$"))
        self.application.add_handler(CallbackQueryHandler(button_cancel, pattern="^cancel$"))

        # Text message handler (for menu buttons)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
        )

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
