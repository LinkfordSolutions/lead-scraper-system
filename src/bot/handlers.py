"""
Telegram bot command handlers with inline and reply keyboards
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .auth import auth_manager
from .exporter import csv_exporter
from .keyboards import get_start_keyboard, get_main_menu_keyboard, get_cancel_keyboard
from ..database.models import ScrapeSession
from ..database.db import get_db_session

logger = logging.getLogger(__name__)

# Conversation states
WAITING_PASSWORD = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    """
    user = update.effective_user
    telegram_id = user.id

    # Check if already authorized
    if auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            f"👋 С возвращением, {user.first_name}!\n\n"
            "Выберите действие из меню ниже:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            f"👋 Добро пожаловать в Lead Scraper System!\n\n"
            f"Привет, {user.first_name}! Я бот для автоматического сбора лидов по Беларуси.\n\n"
            "🎯 Что я умею:\n"
            "• Собираю контакты компаний из 10 ниш\n"
            "• Отправляю данные в удобном CSV формате\n"
            "• Обновляю базу автоматически каждый день\n\n"
            "🔐 Для начала работы необходима авторизация.",
            reply_markup=get_start_keyboard()
        )


async def button_auth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Авторизоваться" button
    """
    query = update.callback_query
    await query.answer()

    user = query.from_user

    # Check if already authorized
    if auth_manager.is_authorized(user.id):
        await query.edit_message_text(
            "✅ Вы уже авторизованы!",
            reply_markup=None
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "🔐 Авторизация\n\n"
        "Пожалуйста, введите пароль доступа:",
        reply_markup=get_cancel_keyboard()
    )

    return WAITING_PASSWORD


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receive password from user
    """
    user = update.effective_user
    telegram_id = user.id
    password = update.message.text.strip()

    # Delete user's message with password for security
    try:
        await update.message.delete()
    except:
        pass

    # Attempt authorization
    success, message = auth_manager.authorize_user(telegram_id, password, user)

    if success:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=f"✅ {message}\n\nВыберите действие из меню:",
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {telegram_id} ({user.username}) authorized successfully")
        return ConversationHandler.END
    else:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=f"{message}\n\nПопробуйте еще раз или нажмите /start для выхода.",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_PASSWORD


async def button_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Информация" button
    """
    query = update.callback_query
    await query.answer()

    info_text = (
        "ℹ️ Lead Scraper System\n\n"
        "🎯 Целевые ниши (10):\n"
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
        "🔄 Обновление: Автоматически каждый день в 03:00 UTC\n\n"
        "📊 Данные в CSV:\n"
        "Название, адрес, телефон, email, сайт, соцсети, рейтинг, геолокация"
    )

    await query.edit_message_text(info_text, reply_markup=get_start_keyboard())


async def button_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Отмена" button
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "❌ Операция отменена.\n\nНажмите /start для возврата в главное меню.",
        reply_markup=None
    )

    return ConversationHandler.END


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages from authorized users
    """
    user = update.effective_user
    telegram_id = user.id
    text = update.message.text

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            "🔐 Для использования бота необходима авторизация.\n\n"
            "Нажмите /start",
            reply_markup=get_start_keyboard()
        )
        return

    # Handle menu buttons
    if text == "📊 Получить лиды":
        await get_leads_handler(update, context)
    elif text == "📈 Статус парсинга":
        await status_handler(update, context)
    elif text == "ℹ️ Помощь":
        await help_handler(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите действие из меню ниже:",
            reply_markup=get_main_menu_keyboard()
        )


async def get_leads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Получить лиды" button
    """
    user = update.effective_user
    telegram_id = user.id

    auth_manager.increment_request_count(telegram_id)

    await update.message.reply_text("⏳ Генерирую файл с лидами...")

    try:
        # Export leads
        file_path, stats = csv_exporter.export_leads()

        if not file_path:
            await update.message.reply_text(
                "❌ В базе данных пока нет лидов.\n\n"
                "Парсинг будет запущен автоматически."
            )
            return

        # Format stats message
        stats_text = f"📊 База лидов Беларуси\n\n"
        stats_text += f"Всего компаний: {stats['total']}\n\n"
        stats_text += "По категориям:\n"
        for category, count in sorted(stats['by_category'].items()):
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
                caption=stats_text
            )

        logger.info(f"User {telegram_id} downloaded leads: {stats['total']} companies")

    except Exception as e:
        logger.error(f"Error exporting leads for user {telegram_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при генерации файла:\n{str(e)}\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Статус парсинга" button
    """
    user = update.effective_user
    telegram_id = user.id

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
                    "Первый автоматический запуск будет в 03:00 UTC."
                )
                return

            # Format status message
            status_icon = {
                'started': '⏳',
                'completed': '✅',
                'failed': '❌'
            }.get(last_session.status, '❓')

            status_text = f"{status_icon} Последний парсинг\n\n"
            status_text += f"Источник: {last_session.source}\n"
            status_text += f"Статус: {last_session.status}\n"
            status_text += f"Начало: {last_session.started_at.strftime('%Y-%m-%d %H:%M')}\n"

            if last_session.completed_at:
                status_text += f"Завершено: {last_session.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
                if last_session.duration_seconds:
                    mins = last_session.duration_seconds // 60
                    secs = last_session.duration_seconds % 60
                    status_text += f"Длительность: {mins}м {secs}с\n"

            status_text += f"\n📊 Результаты:\n"
            status_text += f"  • Обработано: {last_session.total_scraped}\n"
            status_text += f"  • Новых: {last_session.new_companies}\n"
            status_text += f"  • Обновлено: {last_session.updated_companies}\n"

            if last_session.errors_count > 0:
                status_text += f"  • Ошибок: {last_session.errors_count}\n"

            if last_session.error_message:
                status_text += f"\n⚠️ {last_session.error_message[:100]}"

            await update.message.reply_text(status_text)

    except Exception as e:
        logger.error(f"Error getting status for user {telegram_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при получении статуса:\n{str(e)}"
        )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Помощь" button
    """
    help_text = (
        "📖 Справка\n\n"
        "🔘 Кнопки меню:\n\n"
        "📊 Получить лиды\n"
        "Скачать актуальную базу компаний в формате CSV\n\n"
        "📈 Статус парсинга\n"
        "Информация о последней сессии сбора данных\n\n"
        "ℹ️ Помощь\n"
        "Показать эту справку\n\n"
        "💾 Формат данных:\n"
        "CSV файл с полями: название, категория, адрес, город, телефон, email, "
        "сайт, Instagram, рейтинг, отзывы, координаты\n\n"
        "⏰ База обновляется автоматически каждый день в 03:00"
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
