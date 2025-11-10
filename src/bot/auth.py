"""
Authentication and user management for Telegram bot
"""
from datetime import datetime
from sqlalchemy.orm import Session
from telegram import User as TelegramUser

from ..database.models import BotUser
from ..database.db import get_db_session
from ..utils.config import config


class AuthManager:
    """Manage bot user authentication"""

    @staticmethod
    def is_authorized(telegram_id: int) -> bool:
        """
        Check if user is authorized

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if authorized, False otherwise
        """
        with get_db_session() as session:
            user = session.query(BotUser).filter(
                BotUser.telegram_id == telegram_id
            ).first()

            if user and user.is_authorized:
                # Update last active
                user.last_active_at = datetime.utcnow()
                session.commit()
                return True

            return False

    @staticmethod
    def authorize_user(telegram_id: int, password: str, telegram_user: TelegramUser) -> tuple[bool, str]:
        """
        Authorize user with password

        Args:
            telegram_id: Telegram user ID
            password: Provided password
            telegram_user: Telegram user object

        Returns:
            tuple: (success, message)
        """
        # Check password
        if password != config.BOT_PASSWORD:
            return False, "❌ Неверный пароль"

        with get_db_session() as session:
            # Get or create user
            user = session.query(BotUser).filter(
                BotUser.telegram_id == telegram_id
            ).first()

            if user:
                if user.is_authorized:
                    return False, "✅ Вы уже авторизованы"

                # Update existing user
                user.is_authorized = True
                user.last_active_at = datetime.utcnow()
                user.username = telegram_user.username
                user.first_name = telegram_user.first_name
                user.last_name = telegram_user.last_name
            else:
                # Create new user
                user = BotUser(
                    telegram_id=telegram_id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    is_authorized=True,
                    last_active_at=datetime.utcnow()
                )
                session.add(user)

            session.commit()
            return True, f"✅ Авторизация успешна!\n\nДобро пожаловать, {telegram_user.first_name}!"

    @staticmethod
    def get_user_info(telegram_id: int) -> dict:
        """
        Get user information

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: User info or None
        """
        with get_db_session() as session:
            user = session.query(BotUser).filter(
                BotUser.telegram_id == telegram_id
            ).first()

            if not user:
                return None

            return {
                'id': user.id,
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_authorized': user.is_authorized,
                'is_admin': user.is_admin,
                'requests_count': user.requests_count,
                'last_active_at': user.last_active_at,
                'created_at': user.created_at
            }

    @staticmethod
    def increment_request_count(telegram_id: int):
        """
        Increment user request counter

        Args:
            telegram_id: Telegram user ID
        """
        with get_db_session() as session:
            user = session.query(BotUser).filter(
                BotUser.telegram_id == telegram_id
            ).first()

            if user:
                user.requests_count += 1
                user.last_active_at = datetime.utcnow()
                session.commit()

    @staticmethod
    def get_authorized_users() -> list[BotUser]:
        """
        Get all authorized users

        Returns:
            list: List of authorized BotUser objects
        """
        with get_db_session() as session:
            users = session.query(BotUser).filter(
                BotUser.is_authorized == True
            ).all()
            return users


# Create singleton instance
auth_manager = AuthManager()
