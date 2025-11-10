"""
Advanced bot handlers - categories, search, stats, export
"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .keyboards import (
    get_categories_keyboard,
    get_export_format_keyboard,
    get_main_menu_keyboard
)
from .exporter import csv_exporter
from .stats import stats
from .auth import auth_manager
from ..database.models import Category
from ..database.db import get_db_session

logger = logging.getLogger(__name__)

# Conversation states
WAITING_SEARCH_QUERY = 1


async def handle_categories_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Фильтр по категориям' button"""
    telegram_id = update.effective_user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            "❌ Вы не авторизованы. Используйте /start для авторизации."
        )
        return

    await update.message.reply_text(
        "🎯 Выберите категорию для экспорта:",
        reply_markup=get_categories_keyboard()
    )


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection callback"""
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await query.edit_message_text("❌ Вы не авторизованы.")
        return

    callback_data = query.data

    # Get selected category
    if callback_data == "cat_all":
        # Export all categories
        category_ids = None
        category_name = "Все категории"
    else:
        # Extract category key from callback_data (format: cat_auto_service)
        category_key = callback_data.replace("cat_", "")

        # Get category ID from database
        with get_db_session() as session:
            category = session.query(Category).filter(
                Category.name == category_key
            ).first()

            if not category:
                await query.edit_message_text("❌ Категория не найдена")
                return

            category_ids = [category.id]
            category_name = category.name_ru

    # Store selected category in context
    context.user_data['selected_category_ids'] = category_ids
    context.user_data['selected_category_name'] = category_name

    # Ask for export format
    await query.edit_message_text(
        f"✅ Выбрано: **{category_name}**\n\nВыберите формат экспорта:",
        parse_mode='Markdown',
        reply_markup=get_export_format_keyboard()
    )


async def handle_export_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle export format selection"""
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await query.edit_message_text("❌ Вы не авторизованы.")
        return

    # Get selected category from context
    category_ids = context.user_data.get('selected_category_ids')
    category_name = context.user_data.get('selected_category_name', 'Все категории')

    callback_data = query.data

    try:
        await query.edit_message_text("⏳ Экспортирую данные...")

        # Export based on format
        if callback_data == "export_csv":
            file_path, stats_dict = csv_exporter.export_leads(
                category_ids=category_ids
            )
            format_name = "CSV"
        elif callback_data == "export_xlsx":
            file_path, stats_dict = csv_exporter.export_leads_excel(
                category_ids=category_ids
            )
            format_name = "Excel"
        else:
            await query.edit_message_text("❌ Неизвестный формат")
            return

        if not file_path:
            await query.edit_message_text(
                "❌ Нет данных для экспорта по выбранной категории"
            )
            return

        # Prepare message
        file_size = os.path.getsize(file_path)
        file_size_str = csv_exporter.format_file_size(file_size)

        message = (
            f"📊 **Экспорт {format_name}**\n\n"
            f"🎯 Категория: {category_name}\n"
            f"📈 Всего компаний: {stats_dict['total']}\n\n"
        )

        if stats_dict['by_category']:
            message += "**По категориям:**\n"
            for cat, count in sorted(stats_dict['by_category'].items()):
                message += f"  • {cat}: {count}\n"

        message += f"\n📦 Размер: {file_size_str}"

        # Send file
        with open(file_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=telegram_id,
                document=f,
                filename=os.path.basename(file_path),
                caption=message,
                parse_mode='Markdown'
            )

        await query.delete_message()

        logger.info(f"User {telegram_id} exported {format_name}: {stats_dict['total']} companies")

    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Ошибка при экспорте: {str(e)}"
        )


async def handle_statistics_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Статистика' button"""
    telegram_id = update.effective_user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            "❌ Вы не авторизованы. Используйте /start для авторизации."
        )
        return

    try:
        # Get statistics
        db_stats = stats.get_database_stats()

        # Format message
        message = stats.format_stats_message(db_stats)

        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Statistics error: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при получении статистики: {str(e)}"
        )


async def handle_search_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Поиск' button"""
    telegram_id = update.effective_user.id

    # Check authorization
    if not auth_manager.is_authorized(telegram_id):
        await update.message.reply_text(
            "❌ Вы не авторизованы. Используйте /start для авторизации."
        )
        return

    await update.message.reply_text(
        "🔍 **Поиск компаний**\n\n"
        "Введите название компании, телефон, адрес или город для поиска:\n\n"
        "_Например: автосервис, +375, Минск, ул. Ленина_",
        parse_mode='Markdown'
    )

    return WAITING_SEARCH_QUERY


async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search query"""
    telegram_id = update.effective_user.id
    query_text = update.message.text.strip()

    if len(query_text) < 3:
        await update.message.reply_text(
            "❌ Запрос слишком короткий. Минимум 3 символа."
        )
        return WAITING_SEARCH_QUERY

    try:
        # Search companies
        companies = stats.search_companies(query_text, limit=20)

        # Format results
        message = stats.format_search_results(companies)

        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка при поиске: {str(e)}"
        )

    return ConversationHandler.END
