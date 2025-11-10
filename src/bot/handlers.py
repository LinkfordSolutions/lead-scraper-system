"""
Telegram bot command handlers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from .auth import auth_manager
from .exporter import csv_exporter
from ..database.models import ScrapeSession
from ..database.db import get_db_session

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    """
    user = update.effective_user
    telegram_id = user.id

    # Check if already authorized
    if auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            "Вы уже авторизованы в системе.\n\n"
            "📋 Доступные команды:\n"
            "/get_leads - Получить базу лидов (CSV)\n"
            "/status - Статус последнего парсинга\n"
            "/help - Помощь"
        )
    else:
        await update.message.reply_text(
            f"👋 Добро пожаловать в Lead Scraper System!\n\n"
            f"Привет, {user.first_name}! Я бот для автоматического сбора лидов.\n\n"
            "🔐 Для доступа к системе необходима авторизация.\n\n"
            "Используйте команду:\n"
            "/auth <пароль>\n\n"
            "Пример: /auth mypassword123"
        )


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /auth command
    """
    user = update.effective_user
    telegram_id = user.id

    # Check if password provided
    if not context.args:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите пароль.\n\n"
            "Использование: /auth <пароль>\n"
            "Пример: /auth mypassword123"
        )
        return

    password = ' '.join(context.args)

    # Attempt authorization
    success, message = auth_manager.authorize_user(telegram_id, password, user)

    await update.message.reply_text(message)

    if success:
        await update.message.reply_text(
            "📋 Доступные команды:\n"
            "/get_leads - Получить базу лидов (CSV)\n"
            "/status - Статус последнего парсинга\n"
            "/help - Помощь"
        )


async def get_leads_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /get_leads command - export and send CSV
    """
    user = update.effective_user
    telegram_id = user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            "🔐 Доступ запрещен.\n\n"
            "Используйте /auth <пароль> для авторизации."
        )
        return

    # Increment request counter
    auth_manager.increment_request_count(telegram_id)

    await update.message.reply_text("⏳ Генерирую файл с лидами...")

    try:
        # Export leads
        file_path, stats = csv_exporter.export_leads()

        if not file_path:
            await update.message.reply_text(
                "❌ В базе данных пока нет лидов.\n\n"
                "Запустите парсинг для сбора данных."
            )
            return

        # Format stats message
        stats_text = f"📊 Статистика:\n\n"
        stats_text += f"Всего компаний: {stats['total']}\n\n"
        stats_text += "По категориям:\n"
        for category, count in stats['by_category'].items():
            stats_text += f"  • {category}: {count}\n"

        # Get file size
        import os
        file_size = os.path.getsize(file_path)
        file_size_str = csv_exporter.format_file_size(file_size)

        stats_text += f"\nРазмер файла: {file_size_str}"

        # Send file
        with open(file_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=os.path.basename(file_path),
                caption=f"✅ База лидов Беларуси\n\n{stats_text}"
            )

        logger.info(f"User {telegram_id} downloaded leads: {stats['total']} companies")

    except Exception as e:
        logger.error(f"Error exporting leads for user {telegram_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при генерации файла:\n{str(e)}\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command - show last scraping session info
    """
    user = update.effective_user
    telegram_id = user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            "🔐 Доступ запрещен.\n\n"
            "Используйте /auth <пароль> для авторизации."
        )
        return

    auth_manager.increment_request_count(telegram_id)

    try:
        with get_db_session() as session:
            # Get latest scrape session
            last_session = session.query(ScrapeSession).order_by(
                ScrapeSession.started_at.desc()
            ).first()

            if not last_session:
                await update.message.reply_text(
                    "ℹ️ Парсинг еще не запускался.\n\n"
                    "База лидов пуста."
                )
                return

            # Format status message
            status_icon = {
                'started': '⏳',
                'completed': '✅',
                'failed': '❌'
            }.get(last_session.status, '❓')

            status_text = f"{status_icon} Статус последнего парсинга\n\n"
            status_text += f"Источник: {last_session.source}\n"
            status_text += f"Статус: {last_session.status}\n"
            status_text += f"Начало: {last_session.started_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if last_session.completed_at:
                status_text += f"Завершено: {last_session.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                status_text += f"Длительность: {last_session.duration_seconds}с\n"

            status_text += f"\n📊 Результаты:\n"
            status_text += f"  • Всего обработано: {last_session.total_scraped}\n"
            status_text += f"  • Новых компаний: {last_session.new_companies}\n"
            status_text += f"  • Обновлено: {last_session.updated_companies}\n"
            status_text += f"  • Ошибок: {last_session.errors_count}\n"

            if last_session.error_message:
                status_text += f"\n⚠️ Ошибка: {last_session.error_message}"

            await update.message.reply_text(status_text)

    except Exception as e:
        logger.error(f"Error getting status for user {telegram_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при получении статуса:\n{str(e)}"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command
    """
    help_text = (
        "📖 Справка по командам\n\n"
        "🔐 Авторизация:\n"
        "/auth <пароль> - Авторизация в системе\n\n"
        "📊 Работа с данными:\n"
        "/get_leads - Получить актуальную базу лидов в формате CSV\n"
        "/status - Статус последнего парсинга\n\n"
        "ℹ️ Информация:\n"
        "/help - Показать эту справку\n\n"
        "🎯 Целевые ниши:\n"
        "• СТО/детейлинг/шиномонтаж\n"
        "• Мастер на час / электрик / сантехник\n"
        "• Клининговые услуги\n"
        "• Грузоперевозки/переезды\n"
        "• Учителя/репетиторы/курсы\n"
        "• Фитнес/йога/танцы/ЕМС-студии\n"
        "• Фото/видео-студии\n"
        "• Нотариус/юристы/консалтинг\n"
        "• Психологи/коучи\n"
        "• Тату/перманент/пирсинг\n\n"
        "📍 География: Вся Беларусь\n"
        "🔄 Обновление: Автоматически каждый день в 03:00"
    )

    await update.message.reply_text(help_text)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors
    """
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка при обработке вашего запроса.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
