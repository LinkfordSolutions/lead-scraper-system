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
        [KeyboardButton("📊 Получить лиды")],
        [KeyboardButton("📈 Статус парсинга"), KeyboardButton("ℹ️ Помощь")]
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
