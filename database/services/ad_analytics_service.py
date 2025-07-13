# database/services/ad_analytics_service.py

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdCreative, AdEvent, AdEventType
from ..repository import AdEventRepository


class AdAnalyticsService:
    """Сервис для работы с аналитикой рекламы"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_repo = AdEventRepository(session)

    async def record_event(
        self, creative_id: int, event_type: AdEventType, user_id: int = None
    ) -> AdEvent:
        """Запись события рекламы (показ, клик и т.д.)"""
        return await self.event_repo.create(
            creative_id=creative_id, event_type=event_type, user_id=user_id
        )

    async def get_creative_stats(self, creative_id: int, days: int = 30) -> dict:
        """Получение статистики по креативу"""
        start_date = datetime.now() - timedelta(days=days)

        # Получаем количество показов
        impressions_query = select(func.count()).where(
            AdEvent.creative_id == creative_id,
            AdEvent.event_type == AdEventType.IMPRESSION,
            AdEvent.created_at >= start_date,
        )
        impressions_result = await self.session.execute(impressions_query)
        impressions = impressions_result.scalar() or 0

        # Получаем количество кликов
        clicks_query = select(func.count()).where(
            AdEvent.creative_id == creative_id,
            AdEvent.event_type == AdEventType.CLICK,
            AdEvent.created_at >= start_date,
        )
        clicks_result = await self.session.execute(clicks_query)
        clicks = clicks_result.scalar() or 0

        # Вычисляем CTR
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        return {
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 2),
        }

    async def get_campaign_stats(self, campaign_id: int, days: int = 30) -> dict:
        """Получение статистики по кампании"""
        start_date = datetime.now() - timedelta(days=days)

        # Получаем все креативы кампании
        creatives_query = select(AdCreative.id).where(
            AdCreative.campaign_id == campaign_id
        )
        creatives_result = await self.session.execute(creatives_query)
        creative_ids = [row[0] for row in creatives_result.fetchall()]

        if not creative_ids:
            return {
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "spent": Decimal("0.00"),
            }

        # Получаем количество показов
        impressions_query = select(func.count()).where(
            AdEvent.creative_id.in_(creative_ids),
            AdEvent.event_type == AdEventType.IMPRESSION,
            AdEvent.created_at >= start_date,
        )
        impressions_result = await self.session.execute(impressions_query)
        impressions = impressions_result.scalar() or 0

        # Получаем количество кликов
        clicks_query = select(func.count()).where(
            AdEvent.creative_id.in_(creative_ids),
            AdEvent.event_type == AdEventType.CLICK,
            AdEvent.created_at >= start_date,
        )
        clicks_result = await self.session.execute(clicks_query)
        clicks = clicks_result.scalar() or 0

        # Вычисляем CTR
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        # Вычисляем потраченную сумму (предполагаем, что стоимость клика 1 единица)
        spent = Decimal(str(clicks))

        return {
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 2),
            "spent": spent,
        }
