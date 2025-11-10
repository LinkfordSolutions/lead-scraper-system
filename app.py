"""
Main application - runs bot and scheduler together
"""
import asyncio
import sys
import os
import logging
import signal

sys.path.insert(0, os.path.dirname(__file__))

from src.bot.bot import LeadScraperBot
from src.scheduler.task_scheduler import task_scheduler
from src.utils.config import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class Application:
    """Main application"""

    def __init__(self):
        """Initialize application"""
        self.bot = None
        self.running = False

    async def start(self):
        """Start application"""
        logger.info("="*60)
        logger.info("🚀 Starting Lead Scraper System")
        logger.info("="*60)

        # Validate config
        if not config.validate():
            logger.error("❌ Configuration validation failed")
            sys.exit(1)

        # Print config
        config.print_config()

        try:
            # Initialize bot
            logger.info("🤖 Initializing Telegram bot...")
            self.bot = LeadScraperBot()

            # Setup scheduler with bot app
            logger.info("⏰ Setting up task scheduler...")
            task_scheduler.bot_app = self.bot.application
            task_scheduler.setup_jobs()

            # Start scheduler
            task_scheduler.start()

            # Display next run time (after starting)
            next_run = task_scheduler.get_next_run_time()
            if next_run:
                logger.info(f"📅 Next scheduled scraping: {next_run}")

            # Start bot (this will block)
            logger.info("="*60)
            logger.info("✅ System ready!")
            logger.info("="*60)

            self.running = True

            # Run bot
            await self.bot.application.initialize()
            await self.bot.application.post_init(self.bot.application)
            await self.bot.application.start()

            # Start polling
            await self.bot.application.updater.start_polling(
                allowed_updates=None,
                drop_pending_updates=True
            )

            # Keep running
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Stop application"""
        logger.info("⏹️  Stopping application...")

        # Stop scheduler
        task_scheduler.stop()

        # Stop bot
        if self.bot and self.bot.application:
            try:
                await self.bot.application.updater.stop()
                await self.bot.application.stop()
                await self.bot.application.shutdown()
            except:
                pass

        self.running = False
        logger.info("✅ Application stopped")


async def main():
    """Main entry point"""
    app = Application()

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        app.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await app.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
