# database/services/ad_campaign_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdCampaign, CampaignStatus
from ..repository import AdCampaignRepository


class AdCampaignService:
    """Сервис для работы с рекламными кампаниями"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.campaign_repo = AdCampaignRepository(session)

    async def create_campaign(
        self, advertiser_id: int, name: str, daily_budget: float, **kwargs
    ) -> AdCampaign:
        """Создание новой рекламной кампании"""
        return await self.campaign_repo.create(
            advertiser_id=advertiser_id,
            name=name,
            daily_budget=daily_budget,
            status=CampaignStatus.DRAFT,
            **kwargs,
        )

    async def update_campaign_status(
        self, campaign_id: int, status: CampaignStatus
    ) -> AdCampaign | None:
        """Обновление статуса рекламной кампании"""
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            return None

        return await self.campaign_repo.update(campaign, status=status)

    async def get_campaign(self, campaign_id: int) -> AdCampaign | None:
        """Получение рекламной кампании по ID"""
        return await self.campaign_repo.get_by_id(campaign_id)

    async def get_advertiser_campaigns(
        self, advertiser_id: int, status: CampaignStatus = None
    ) -> list[AdCampaign]:
        """Получение всех кампаний рекламодателя"""
        return await self.campaign_repo.get_by_advertiser(advertiser_id)

    async def update_campaign(self, campaign_id: int, **kwargs) -> AdCampaign | None:
        """Обновление данных рекламной кампании"""
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            return None

        return await self.campaign_repo.update(campaign, **kwargs)

    async def get_all_campaigns(self) -> list[AdCampaign]:
        """Получение всех рекламных кампаний"""
        return await self.campaign_repo.get_all()

    async def get_campaigns_by_advertiser(self, advertiser_id: int) -> list[AdCampaign]:
        """Получение всех кампаний рекламодателя"""
        return await self.campaign_repo.get_by_advertiser(advertiser_id)
