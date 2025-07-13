# database/analytics.py
"""
Аналитические запросы - НЕ дублируют CRUD операции
Включает аналитику пользователей, групп и рекламной системы
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AdAnalytics,
    AdCampaign,
    AdCampaignStatus,
    AdCreative,
    AdEventType,
    AdPlacement,
    Advertiser,
    Group,
    GroupMember,
    MemberStatus,
    Transaction,
    TransactionType,
    User,
    UserStatus,
)


class UserAnalytics:
    """Аналитика пользователей"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_top_inviters(self, limit: int = 10) -> list[dict[str, Any]]:
        """Топ пользователей по приглашениям"""
        stmt = (
            select(User.id, User.username, User.first_name, User.invitation_count)
            .where(
                and_(
                    User.status == UserStatus.ACTIVE,
                    not User.is_deleted,
                    User.invitation_count > 0,
                )
            )
            .order_by(desc(User.invitation_count))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [
            {
                "user_id": row.id,
                "username": row.username,
                "first_name": row.first_name,
                "invitations": row.invitation_count,
            }
            for row in result.fetchall()
        ]

    async def get_user_growth_stats(self, days: int = 30) -> dict[str, Any]:
        """Статистика роста пользователей"""
        start_date = datetime.now() - timedelta(days=days)

        # Новые пользователи
        new_users = await self.session.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= start_date, not User.is_deleted)
            )
        )

        # Активные пользователи
        active_users = await self.session.execute(
            select(func.count(User.id)).where(
                and_(
                    User.last_active_at >= start_date,
                    User.status == UserStatus.ACTIVE,
                    not User.is_deleted,
                )
            )
        )

        # Общее количество
        total_users = await self.session.execute(
            select(func.count(User.id)).where(
                and_(User.status == UserStatus.ACTIVE, not User.is_deleted)
            )
        )

        return {
            "period_days": days,
            "new_users": new_users.scalar(),
            "active_users": active_users.scalar(),
            "total_users": total_users.scalar(),
        }


class GroupAnalytics:
    """Аналитика групп"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_group_stats(self, group_id: int) -> dict[str, Any]:
        """Детальная статистика группы"""
        # Общие участники
        total_members = await self.session.execute(
            select(func.count(GroupMember.id)).where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.status.in_(
                        [MemberStatus.MEMBER, MemberStatus.ADMIN, MemberStatus.CREATOR]
                    ),
                )
            )
        )

        # Новые участники за неделю
        week_ago = datetime.now() - timedelta(days=7)
        new_members = await self.session.execute(
            select(func.count(GroupMember.id)).where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.joined_at >= week_ago,
                    GroupMember.status.in_(
                        [MemberStatus.MEMBER, MemberStatus.ADMIN, MemberStatus.CREATOR]
                    ),
                )
            )
        )

        # Участники с предупреждениями
        warned_members = await self.session.execute(
            select(func.count(GroupMember.id)).where(
                and_(GroupMember.group_id == group_id, GroupMember.warnings_count > 0)
            )
        )

        return {
            "total_members": total_members.scalar(),
            "new_members_week": new_members.scalar(),
            "warned_members": warned_members.scalar(),
        }


class AdvertiserAnalytics:
    """Аналитика рекламодателей"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_top_advertisers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Топ рекламодателей по расходам"""
        # Подзапрос для получения суммы расходов по каждому рекламодателю
        spend_subquery = (
            select(
                Transaction.advertiser_id,
                func.sum(Transaction.amount).label("total_spend"),
            )
            .where(Transaction.type == TransactionType.SPEND)
            .group_by(Transaction.advertiser_id)
            .subquery()
        )

        # Основной запрос с джойном на подзапрос
        stmt = (
            select(
                Advertiser.id,
                Advertiser.company_name,
                Advertiser.balance,
                func.abs(spend_subquery.c.total_spend).label("total_spend"),
            )
            .join(spend_subquery, Advertiser.id == spend_subquery.c.advertiser_id)
            .order_by(desc("total_spend"))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [
            {
                "advertiser_id": row.id,
                "company_name": row.company_name,
                "balance": row.balance,
                "total_spend": row.total_spend,
            }
            for row in result.fetchall()
        ]

    async def get_advertiser_growth_stats(self, days: int = 30) -> dict[str, Any]:
        """Статистика роста рекламодателей"""
        start_date = datetime.now() - timedelta(days=days)

        # Новые рекламодатели
        new_advertisers = await self.session.execute(
            select(func.count(Advertiser.id)).where(Advertiser.created_at >= start_date)
        )

        # Общее количество
        total_advertisers = await self.session.execute(
            select(func.count(Advertiser.id))
        )

        # Общий баланс всех рекламодателей
        total_balance = await self.session.execute(select(func.sum(Advertiser.balance)))

        # Общие расходы за период
        total_spend = await self.session.execute(
            select(func.sum(func.abs(Transaction.amount))).where(
                and_(
                    Transaction.type == TransactionType.SPEND,
                    Transaction.created_at >= start_date,
                )
            )
        )

        return {
            "period_days": days,
            "new_advertisers": new_advertisers.scalar() or 0,
            "total_advertisers": total_advertisers.scalar() or 0,
            "total_balance": total_balance.scalar() or Decimal("0.00"),
            "total_spend": total_spend.scalar() or Decimal("0.00"),
        }


class CampaignAnalytics:
    """Аналитика рекламных кампаний"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_campaign_performance(self, campaign_id: int) -> dict[str, Any]:
        """Детальная статистика кампании"""
        # Получаем информацию о кампании
        campaign_info = await self.session.execute(
            select(
                AdCampaign.id,
                AdCampaign.name,
                AdCampaign.budget,
                AdCampaign.spent_amount,
                AdCampaign.start_date,
                AdCampaign.end_date,
                AdCampaign.status,
            ).where(AdCampaign.id == campaign_id)
        )
        campaign = campaign_info.fetchone()
        if not campaign:
            return {}

        # Получаем все креативы кампании
        creatives_query = await self.session.execute(
            select(AdCreative.id).where(AdCreative.campaign_id == campaign_id)
        )
        creative_ids = [row.id for row in creatives_query.fetchall()]

        if not creative_ids:
            return {
                "campaign_id": campaign.id,
                "name": campaign.name,
                "budget": campaign.budget,
                "spent_amount": campaign.spent_amount,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "status": campaign.status.value,
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "groups_count": 0,
            }

        # Подсчитываем показы и клики
        events_stats = await self.session.execute(
            select(
                func.count(
                    case((AdAnalytics.event_type == AdEventType.IMPRESSION, 1))
                ).label("impressions"),
                func.count(
                    case((AdAnalytics.event_type == AdEventType.CLICK, 1))
                ).label("clicks"),
            ).where(AdAnalytics.creative_id.in_(creative_ids))
        )
        stats = events_stats.fetchone()

        # Количество групп, в которых размещена реклама
        groups_count = await self.session.execute(
            select(func.count(distinct(AdPlacement.group_id))).where(
                AdPlacement.campaign_id == campaign_id
            )
        )

        # Рассчитываем CTR
        impressions = stats.impressions or 0
        clicks = stats.clicks or 0
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "budget": campaign.budget,
            "spent_amount": campaign.spent_amount,
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "status": campaign.status.value,
            "impressions": impressions,
            "clicks": clicks,
            "ctr": ctr,
            "groups_count": groups_count.scalar() or 0,
        }

    async def get_top_campaigns(self, limit: int = 10) -> list[dict[str, Any]]:
        """Топ кампаний по эффективности (CTR)"""
        # Получаем все активные кампании
        campaigns_query = await self.session.execute(
            select(AdCampaign.id, AdCampaign.name, AdCampaign.spent_amount)
            .where(AdCampaign.status == AdCampaignStatus.ACTIVE)
            .limit(limit)
        )
        campaigns = campaigns_query.fetchall()

        result = []
        for campaign in campaigns:
            # Для каждой кампании получаем статистику
            stats = await self.get_campaign_performance(campaign.id)
            if stats and stats.get("impressions", 0) > 0:  # Только кампании с показами
                result.append(stats)

        # Сортируем по CTR
        return sorted(result, key=lambda x: x.get("ctr", 0), reverse=True)[:limit]


class GroupAdAnalytics:
    """Аналитика рекламы в группах"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_group_ad_stats(self, group_id: int) -> dict[str, Any]:
        """Статистика рекламы в группе"""
        # Получаем информацию о группе
        group_info = await self.session.execute(
            select(Group.id, Group.title).where(Group.id == group_id)
        )
        group = group_info.fetchone()
        if not group:
            return {}

        # Активные размещения в группе
        active_placements = await self.session.execute(
            select(func.count(AdPlacement.id))
            .join(AdCampaign, AdPlacement.campaign_id == AdCampaign.id)
            .where(
                and_(
                    AdPlacement.group_id == group_id,
                    AdCampaign.status == AdCampaignStatus.ACTIVE,
                    AdCampaign.start_date <= datetime.now(),
                    AdCampaign.end_date >= datetime.now(),
                )
            )
        )

        # Статистика показов и кликов
        events_stats = await self.session.execute(
            select(
                func.count(
                    case((AdAnalytics.event_type == AdEventType.IMPRESSION, 1))
                ).label("impressions"),
                func.count(
                    case((AdAnalytics.event_type == AdEventType.CLICK, 1))
                ).label("clicks"),
            ).where(AdAnalytics.group_id == group_id)
        )
        stats = events_stats.fetchone()

        # Рассчитываем CTR
        impressions = stats.impressions or 0
        clicks = stats.clicks or 0
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        # Статистика за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        recent_stats = await self.session.execute(
            select(
                func.count(
                    case((AdAnalytics.event_type == AdEventType.IMPRESSION, 1))
                ).label("impressions"),
                func.count(
                    case((AdAnalytics.event_type == AdEventType.CLICK, 1))
                ).label("clicks"),
            ).where(
                and_(
                    AdAnalytics.group_id == group_id,
                    AdAnalytics.event_time >= week_ago,
                )
            )
        )
        recent = recent_stats.fetchone()

        return {
            "group_id": group.id,
            "title": group.title,
            "active_placements": active_placements.scalar() or 0,
            "total_impressions": impressions,
            "total_clicks": clicks,
            "ctr": ctr,
            "recent_impressions": recent.impressions or 0,
            "recent_clicks": recent.clicks or 0,
        }

    async def get_top_ad_groups(self, limit: int = 10) -> list[dict[str, Any]]:
        """Топ групп по эффективности рекламы (CTR)"""
        # Получаем группы с наибольшим количеством показов
        groups_query = await self.session.execute(
            select(
                AdAnalytics.group_id, func.count(AdAnalytics.id).label("events_count")
            )
            .group_by(AdAnalytics.group_id)
            .order_by(desc("events_count"))
            .limit(limit * 2)  # Берем с запасом, так как не все могут иметь клики
        )
        group_ids = [row.group_id for row in groups_query.fetchall()]

        result = []
        for group_id in group_ids:
            # Для каждой группы получаем статистику
            stats = await self.get_group_ad_stats(group_id)
            if (
                stats and stats.get("total_impressions", 0) > 0
            ):  # Только группы с показами
                result.append(stats)

        # Сортируем по CTR
        return sorted(result, key=lambda x: x.get("ctr", 0), reverse=True)[:limit]