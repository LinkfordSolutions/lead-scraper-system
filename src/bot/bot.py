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
from src.bot.advanced_handlers import (
    handle_categories_button,
    handle_category_selection,
    handle_export_format,
    handle_statistics_button,
    handle_search_button,
    handle_search_query,
    WAITING_SEARCH_QUERY
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
        self.build_application()

    def build_application(self):
        """Build the application and setup handlers"""
        # Create application
        self.application = Application.builder().token(self.token).build()

        # Setup handlers
        self.setup_handlers()

        # Add post init callback
        self.application.post_init = self.post_init

        logger.info("✅ Bot application built")

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

        # Search conversation handler
        search_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^🔍 Поиск$"), handle_search_button)
            ],
            states={
                WAITING_SEARCH_QUERY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query)
                ],
            },
            fallbacks=[
                CommandHandler("start", start_command),
                MessageHandler(filters.Regex("^(📊|📈|ℹ️|🎯)"), handle_text_message)
            ],
        )
        self.application.add_handler(search_conv_handler)

        # Callback query handlers (inline buttons)
        self.application.add_handler(CallbackQueryHandler(button_info, pattern="^info$"))
        self.application.add_handler(CallbackQueryHandler(button_cancel, pattern="^cancel$"))

        # Category selection handlers
        self.application.add_handler(CallbackQueryHandler(handle_category_selection, pattern="^cat_"))
        self.application.add_handler(CallbackQueryHandler(handle_export_format, pattern="^export_"))

        # Menu button handlers (must be before general text handler)
        self.application.add_handler(
            MessageHandler(filters.Regex("^🎯 Фильтр по категориям$"), handle_categories_button)
        )
        self.application.add_handler(
            MessageHandler(filters.Regex("^📈 Статистика$"), handle_statistics_button)
        )

        # Text message handler (for menu buttons) - should be last
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

        # Start polling (application already built in __init__)
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
