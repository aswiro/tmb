from database.unit_of_work import UnitOfWork
from loguru import logger

from config.settings import Settings


class AdminManager:
    """
    Класс для управления администраторами бота.
    Использует Unit of Work паттерн и сервисы для работы с БД.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Инициализация менеджера администраторов.

        Args:
            uow: Unit of Work для управления транзакциями
        """
        self.uow = uow

    async def get_admin_ids_from_db(self) -> list[int]:
        """
        Получает список ID администраторов из базы данных.

        Возвращает список user_id пользователей, которые являются администраторами
        или создателями в любой из групп.

        Returns:
            List[int]: Список ID администраторов
        """
        try:
            async with self.uow:
                admin_ids = await self.uow.group_service.get_all_admin_ids()
                return admin_ids

        except Exception as e:
            logger.error(f"Ошибка при получении администраторов из БД: {e}")
            # Возвращаем пустой список в случае ошибки
            return []

    async def update_admin_ids_in_settings(self, settings: Settings):
        """
        Обновляет список администраторов в настройках приложения.

        Получает актуальный список администраторов из БД и обновляет
        поле bot_admin_ids в переданном объекте settings.

        Args:
            settings: Объект настроек для обновления

        Returns:
            List[int]: Обновленный список администраторов
        """
        admin_ids = await self.get_admin_ids_from_db()
        settings.bot_admin_ids = admin_ids

        logger.info(f"Обновлен список администраторов: {admin_ids}")
        return admin_ids
