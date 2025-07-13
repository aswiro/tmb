# database/services/ad_placement_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdPlacement
from ..repository import AdPlacementRepository


class AdPlacementService:
    """Сервис для работы с размещениями рекламы"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.placement_repo = AdPlacementRepository(session)

    async def create_placement(
        self, campaign_id: int, group_id: int, **kwargs
    ) -> AdPlacement:
        """Создание нового размещения рекламы"""
        return await self.placement_repo.create(
            campaign_id=campaign_id, group_id=group_id, **kwargs
        )

    async def delete_placement(self, placement_id: int) -> bool:
        """Удаление размещения рекламы"""
        placement = await self.placement_repo.get_by_id(placement_id)
        if not placement:
            return False

        await self.placement_repo.delete(placement)
        return True

    async def get_campaign_placements(self, campaign_id: int) -> list[AdPlacement]:
        """Получение всех размещений кампании"""
        return await self.placement_repo.get_by_campaign_id(campaign_id)

    async def get_group_placements(self, group_id: int) -> list[AdPlacement]:
        """Получение всех размещений в группе"""
        return await self.placement_repo.get_by_group_id(group_id)
