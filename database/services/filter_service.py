# database/services/filter_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import FilterRule
from ..repository import FilterRuleRepository


class FilterService:
    """Сервис для работы с фильтрами групп"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.filter_repo = FilterRuleRepository(session)

    async def get_group_filters(self, group_id: int) -> FilterRule | None:
        """Получение фильтров по группе"""
        return await self.filter_repo.get_by_group_id(group_id)

    async def update_filter_by_name(
        self, group_id: int, filter_name: str, value
    ) -> bool:
        """Обновление фильтра по группе и названию фильтра"""
        return await self.filter_repo.update_by_column_name(
            group_id, filter_name, value
        )

    async def create_default_filters(self, group_id: int) -> FilterRule:
        """Создание фильтров по умолчанию для новой группы"""
        return await self.filter_repo.create(id=group_id)
