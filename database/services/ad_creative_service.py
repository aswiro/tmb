# database/services/ad_creative_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdCreative, CreativeStatus
from ..repository import AdCreativeRepository


class AdCreativeService:
    """Сервис для работы с рекламными креативами"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.creative_repo = AdCreativeRepository(session)

    async def create_creative(
        self, campaign_id: int, content: str, **kwargs
    ) -> AdCreative:
        """Создание нового рекламного креатива"""
        return await self.creative_repo.create(
            campaign_id=campaign_id,
            content=content,
            status=CreativeStatus.PENDING,
            **kwargs,
        )

    async def moderate_creative(
        self, creative_id: int, status: CreativeStatus, rejection_reason: str = None
    ) -> AdCreative | None:
        """Модерация рекламного креатива"""
        creative = await self.creative_repo.get_by_id(creative_id)
        if not creative:
            return None

        update_data = {"status": status}
        if status == CreativeStatus.REJECTED and rejection_reason:
            update_data["rejection_reason"] = rejection_reason

        return await self.creative_repo.update(creative, **update_data)

    async def get_creative(self, creative_id: int) -> AdCreative | None:
        """Получение рекламного креатива по ID"""
        return await self.creative_repo.get_by_id(creative_id)

    async def get_campaign_creatives(
        self, campaign_id: int, status: CreativeStatus = None
    ) -> list[AdCreative]:
        """Получение всех креативов кампании"""
        return await self.creative_repo.get_by_campaign_id(campaign_id, status)

    async def get_pending_moderation(self) -> list[AdCreative]:
        """Получение всех креативов, ожидающих модерации"""
        return await self.creative_repo.get_by_status(CreativeStatus.PENDING)
