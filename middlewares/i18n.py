from typing import Any

from aiogram.enums import ChatType
from aiogram.types import Chat, Message, TelegramObject, User
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import I18nMiddleware as BaseI18nMiddleware


class I18nMiddleware(BaseI18nMiddleware):
    """Custom I18n middleware for handling translations.

    This middleware extends aiogram's built-in I18nMiddleware to check for
    user's language_code in the database first, and if not found, uses the
    language_code from the Telegram API.
    It only works in private chat mode, not in group or supergroup chats.
    """

    def __init__(self, i18n: I18n):
        super().__init__(i18n)

    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        """Get user locale from database or fallback to Telegram API."""
        # Get user and chat from event
        user = data.get("event_from_user")
        chat = None

        # Try to get chat from event
        if isinstance(event, Message):
            chat = event.chat
        elif "event_chat" in data:
            chat = data.get("event_chat")

        # Skip middleware for non-private chats, use default locale
        if chat and isinstance(chat, Chat) and chat.type != ChatType.PRIVATE:
            return "ru"

        if user and isinstance(user, User):
            locale = "ru"  # Default locale

            # Try to get user's language from database first
            try:
                # Use UnitOfWork from data that was added by DbSessionMiddleware
                uow = data.get("uow")
                if uow:
                    db_user = await uow.user_service.get_user_by_id(user.id)
                    if db_user and db_user.language_code:
                        locale = db_user.language_code
                    else:
                        # Fallback to Telegram API language_code
                        locale = user.language_code or "ru"
                else:
                    # Fallback to Telegram API if UnitOfWork is not available
                    locale = user.language_code or "ru"
            except Exception:
                # In case of database error, fallback to Telegram API
                locale = user.language_code or "ru"

            # Ensure we only use supported locales
            if locale not in ["ru", "en"]:
                locale = "ru"

            return locale

        return "ru"
