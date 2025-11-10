"""
Task scheduler for automated scraping
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..parsers.parser_manager import parser_manager
from ..parsers.twogis_parser import TwoGISParser
from ..bot.exporter import csv_exporter
from ..bot.auth import auth_manager
from ..utils.config import config

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled tasks"""

    def __init__(self, bot_app=None):
        """
        Initialize scheduler

        Args:
            bot_app: Telegram bot application (for sending messages)
        """
        self.scheduler = AsyncIOScheduler()
        self.bot_app = bot_app
        self.is_running = False

    def setup_jobs(self):
        """Setup all scheduled jobs"""
        # Parse schedule time from config (e.g., "03:00")
        schedule_time = config.SCRAPING_TIME
        hour, minute = map(int, schedule_time.split(':'))

        # Daily scraping job
        self.scheduler.add_job(
            self.run_daily_scraping,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_scraping',
            name='Daily Lead Scraping',
            replace_existing=True
        )

        logger.info(f"✅ Scheduled daily scraping at {schedule_time} UTC")

    async def run_daily_scraping(self):
        """
        Run daily scraping task
        """
        logger.info("="*60)
        logger.info("🕒 Starting scheduled scraping")
        logger.info("="*60)

        try:
            # Register all parsers
            logger.info("📦 Registering parsers...")

            # 2GIS Parser
            if config.TWOGIS_API_KEY and config.TWOGIS_API_KEY != 'your_2gis_api_key_here':
                logger.info("  ✅ 2GIS parser")
                twogis = TwoGISParser(api_key=config.TWOGIS_API_KEY)
                parser_manager.register_parser(twogis)
            else:
                logger.info("  ⚠️  2GIS parser skipped (no API key)")

            # Yandex Maps Parser
            if hasattr(config, 'YANDEX_API_KEY') and config.YANDEX_API_KEY:
                from ..parsers.yandex_parser import YandexMapsParser
                logger.info("  ✅ Yandex Maps parser")
                yandex = YandexMapsParser(api_key=config.YANDEX_API_KEY)
                parser_manager.register_parser(yandex)
            else:
                logger.info("  ⚠️  Yandex Maps parser skipped (no API key)")

            # EGR Parser (no API key needed)
            from ..parsers.egr_parser import EGRParser
            logger.info("  ✅ EGR.gov.by parser")
            egr = EGRParser()
            parser_manager.register_parser(egr)

            # Onliner Parser (no API key needed)
            from ..parsers.onliner_parser import OnlinerParser
            logger.info("  ✅ Onliner.by parser")
            onliner = OnlinerParser()
            parser_manager.register_parser(onliner)

            # Deal Parser (no API key needed)
            from ..parsers.deal_parser import DealParser
            logger.info("  ✅ Deal.by parser")
            deal = DealParser()
            parser_manager.register_parser(deal)

            # Instagram Parser (optional)
            if hasattr(config, 'INSTAGRAM_SESSION_ID') and config.INSTAGRAM_SESSION_ID:
                from ..parsers.instagram_parser import InstagramParser
                logger.info("  ✅ Instagram parser")
                instagram = InstagramParser(session_id=config.INSTAGRAM_SESSION_ID)
                parser_manager.register_parser(instagram)
            else:
                logger.info("  ⚠️  Instagram parser skipped (no session ID)")

            # Run scraping
            logger.info("🔍 Starting scraping...")
            categories = config.get_enabled_niches()
            await parser_manager.run_all_parsers(categories)

            logger.info("✅ Scheduled scraping completed")

            # Send results to users
            await self.send_results_to_users()

        except Exception as e:
            logger.error(f"❌ Scheduled scraping failed: {e}", exc_info=True)

    async def send_results_to_users(self):
        """
        Export CSV and send to all authorized users
        """
        if not self.bot_app:
            logger.warning("Bot app not configured, skipping auto-send")
            return

        try:
            logger.info("📊 Exporting leads to CSV...")

            # Export leads
            file_path, stats = csv_exporter.export_leads()

            if not file_path:
                logger.warning("No leads to export")
                return

            # Get authorized users
            users = auth_manager.get_authorized_users()

            if not users:
                logger.info("No authorized users to send to")
                return

            # Prepare message
            import os
            file_size = os.path.getsize(file_path)
            file_size_str = csv_exporter.format_file_size(file_size)

            message = (
                f"🔄 Автоматическое обновление базы лидов\n\n"
                f"📊 Всего компаний: {stats['total']}\n\n"
                f"По категориям:\n"
            )

            for category, count in sorted(stats['by_category'].items()):
                message += f"  • {category}: {count}\n"

            message += f"\nРазмер: {file_size_str}"

            # Send to all users
            sent_count = 0
            for user in users:
                try:
                    with open(file_path, 'rb') as f:
                        await self.bot_app.bot.send_document(
                            chat_id=user.telegram_id,
                            document=f,
                            filename=os.path.basename(file_path),
                            caption=message
                        )
                    sent_count += 1
                    logger.info(f"Sent CSV to user {user.telegram_id}")

                    # Small delay between sends
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Failed to send to user {user.telegram_id}: {e}")

            logger.info(f"✅ Sent CSV to {sent_count}/{len(users)} users")

        except Exception as e:
            logger.error(f"Failed to send results: {e}", exc_info=True)

    def start(self):
        """Start scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Scheduler started")

    def stop(self):
        """Stop scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("⏹️  Scheduler stopped")

    def get_next_run_time(self, job_id: str = 'daily_scraping'):
        """
        Get next run time for a job

        Args:
            job_id: Job ID

        Returns:
            Next run time or None
        """
        if not self.is_running:
            return None

        job = self.scheduler.get_job(job_id)
        if job and hasattr(job, 'next_run_time'):
            return job.next_run_time
        return None

    async def trigger_manual_scraping(self):
        """Manually trigger scraping (for testing)"""
        logger.info("🔧 Manual scraping triggered")
        await self.run_daily_scraping()


# Global scheduler instance
task_scheduler = TaskScheduler()
