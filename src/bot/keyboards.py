"""
Telegram bot keyboards (inline and reply)
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard():
    """
    Get inline keyboard for start command (unauthorized users)
    """
    keyboard = [
        [InlineKeyboardButton("🔐 Авторизоваться", callback_data="auth_start")],
        [InlineKeyboardButton("ℹ️ Информация о системе", callback_data="info")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard():
    """
    Get reply keyboard for main menu (authorized users)
    """
    keyboard = [
        [KeyboardButton("📊 Получить лиды"), KeyboardButton("🔍 Поиск")],
        [KeyboardButton("🎯 Фильтр по категориям"), KeyboardButton("📈 Статистика")],
        [KeyboardButton("📋 Статус парсинга"), KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_cancel_keyboard():
    """
    Get inline keyboard with cancel button
    """
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_categories_keyboard():
    """
    Get inline keyboard for category selection
    """
    # Category names in Russian
    category_names = {
        'auto_service': '🚗 Автосервис',
        'handyman': '🔧 Мастер на час',
        'cleaning': '🧹 Клининг',
        'moving': '📦 Грузоперевозки',
        'education': '📚 Репетиторы',
        'fitness': '💪 Фитнес',
        'photo_video': '📸 Фото/Видео',
        'legal': '⚖️ Юристы',
        'psychology': '🧠 Психологи',
        'tattoo': '🎨 Тату'
    }

    keyboard = []
    # 2 categories per row
    row = []
    for key, name in category_names.items():
        row.append(InlineKeyboardButton(name, callback_data=f"cat_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:  # Add remaining button if odd number
        keyboard.append(row)

    # Add "All categories" and "Cancel" buttons
    keyboard.append([InlineKeyboardButton("✅ Все категории", callback_data="cat_all")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(keyboard)


def get_export_format_keyboard():
    """
    Get inline keyboard for export format selection
    """
    keyboard = [
        [InlineKeyboardButton("📄 CSV", callback_data="export_csv")],
        [InlineKeyboardButton("📊 Excel (XLSX)", callback_data="export_xlsx")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)
