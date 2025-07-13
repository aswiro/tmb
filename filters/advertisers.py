from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, Update
from database.db_main import get_session
from database.services.advertiser_service import AdvertiserService


class AdvertiserFilter(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь рекламодателем.
    """

    async def __call__(self, update: Update) -> bool:
        """
        Проверяет, является ли отправитель сообщения рекламодателем.

        Args:
            update: Обновление от пользователя

        Returns:
            bool: True, если пользователь является рекламодателем
        """
        if isinstance(update, (Message, CallbackQuery)):
            user_id = update.from_user.id
        else:
            return False

        if not user_id:
            return False

        async with get_session() as session:
            advertiser_service = AdvertiserService(session)
            advertiser = await advertiser_service.get_advertiser(user_id)
            return advertiser is not None
