from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, Update
from config.settings import settings


class AdminFilter(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором бота.
    """

    async def __call__(self, update: Update) -> bool:
        """
        Проверяет, является ли отправитель сообщения администратором бота.

        Args:
            message: Сообщение от пользователя

        Returns:
            bool: True, если пользователь является администратором
        """
        if isinstance(update, (Message, CallbackQuery)):
            user_id = update.from_user.id
        if not user_id:
            return False

        return user_id in settings.bot_admin_ids
