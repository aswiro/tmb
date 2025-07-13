# database/services/post_analytics_service.py

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdminPost, PostAnalytics, PostStatus
from ..repository import AdminPostRepository


class PostAnalyticsService:
    """Сервис для работы с аналитикой постов"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.admin_post_repo = AdminPostRepository(session)

    async def track_view(self, post_id: int, group_id: int) -> bool:
        """Отслеживание просмотра поста"""
        try:
            # Получаем или создаем запись аналитики
            analytics = await self._get_or_create_analytics(post_id, group_id)

            # Увеличиваем счетчик просмотров
            analytics.views_count += 1
            await self.session.flush()

            return True
        except Exception:
            return False

    async def track_click(self, post_id: int, group_id: int) -> bool:
        """Отслеживание клика по посту"""
        try:
            # Получаем или создаем запись аналитики
            analytics = await self._get_or_create_analytics(post_id, group_id)

            # Увеличиваем счетчик кликов
            analytics.clicks_count += 1
            await self.session.flush()

            return True
        except Exception:
            return False

    async def track_share(self, post_id: int, group_id: int) -> bool:
        """Отслеживание репоста/пересылки поста"""
        try:
            # Получаем или создаем запись аналитики
            analytics = await self._get_or_create_analytics(post_id, group_id)

            # Увеличиваем счетчик репостов
            analytics.shares_count += 1
            await self.session.flush()

            return True
        except Exception:
            return False

    async def track_reaction(self, post_id: int, group_id: int, reaction: str) -> bool:
        """Отслеживание реакции на пост"""
        try:
            # Получаем или создаем запись аналитики
            analytics = await self._get_or_create_analytics(post_id, group_id)

            # Обновляем счетчик реакций
            if analytics.reactions is None:
                analytics.reactions = {}

            analytics.reactions[reaction] = analytics.reactions.get(reaction, 0) + 1
            await self.session.flush()

            return True
        except Exception:
            return False

    async def track_view_duration(
        self, post_id: int, group_id: int, duration_seconds: int
    ) -> bool:
        """Отслеживание времени просмотра поста"""
        try:
            # Получаем или создаем запись аналитики
            analytics = await self._get_or_create_analytics(post_id, group_id)

            # Обновляем среднее время просмотра
            if analytics.view_duration is None:
                analytics.view_duration = duration_seconds
            else:
                # Простое среднее арифметическое
                analytics.view_duration = (
                    analytics.view_duration + duration_seconds
                ) // 2

            await self.session.flush()
            return True
        except Exception:
            return False

    async def get_post_analytics(self, post_id: int) -> dict[str, Any]:
        """Получение аналитики по конкретному посту"""
        try:
            # Получаем все записи аналитики для поста
            query = select(PostAnalytics).where(PostAnalytics.post_id == post_id)
            result = await self.session.execute(query)
            analytics_records = result.scalars().all()

            if not analytics_records:
                return {
                    "total_views": 0,
                    "total_clicks": 0,
                    "total_shares": 0,
                    "total_reactions": {},
                    "average_ctr": 0.0,
                    "average_engagement": 0.0,
                    "groups_count": 0,
                    "by_groups": [],
                }

            # Агрегируем данные
            total_views = sum(record.views_count for record in analytics_records)
            total_clicks = sum(record.clicks_count for record in analytics_records)
            total_shares = sum(record.shares_count for record in analytics_records)

            # Объединяем реакции
            total_reactions = {}
            for record in analytics_records:
                if record.reactions:
                    for reaction, count in record.reactions.items():
                        total_reactions[reaction] = (
                            total_reactions.get(reaction, 0) + count
                        )

            # Вычисляем метрики
            average_ctr = (total_clicks / total_views * 100) if total_views > 0 else 0.0
            total_reaction_count = sum(total_reactions.values())
            average_engagement = (
                (
                    (total_clicks + total_shares + total_reaction_count)
                    / total_views
                    * 100
                )
                if total_views > 0
                else 0.0
            )

            # Данные по группам
            by_groups = []
            for record in analytics_records:
                by_groups.append(
                    {
                        "group_id": record.group_id,
                        "views": record.views_count,
                        "clicks": record.clicks_count,
                        "shares": record.shares_count,
                        "reactions": record.reactions or {},
                        "ctr": record.click_through_rate,
                        "engagement": record.engagement_rate,
                        "view_duration": record.view_duration,
                    }
                )

            return {
                "total_views": total_views,
                "total_clicks": total_clicks,
                "total_shares": total_shares,
                "total_reactions": total_reactions,
                "average_ctr": round(average_ctr, 2),
                "average_engagement": round(average_engagement, 2),
                "groups_count": len(analytics_records),
                "by_groups": by_groups,
            }
        except Exception:
            return {}

    async def get_analytics_summary(  # noqa: C901
        self, date_from: datetime, date_to: datetime
    ) -> dict[str, Any]:
        """Получение сводной аналитики за период"""
        try:
            # Получаем все посты за период
            posts_query = select(AdminPost).where(
                AdminPost.published_at.between(date_from, date_to),
                AdminPost.status == PostStatus.PUBLISHED,
            )
            posts_result = await self.session.execute(posts_query)
            posts = posts_result.scalars().all()

            if not posts:
                return {
                    "period": {
                        "from": date_from.isoformat(),
                        "to": date_to.isoformat(),
                    },
                    "posts_count": 0,
                    "total_views": 0,
                    "total_clicks": 0,
                    "total_shares": 0,
                    "total_reactions": {},
                    "average_ctr": 0.0,
                    "average_engagement": 0.0,
                    "top_posts": [],
                }

            post_ids = [post.id for post in posts]

            # Получаем аналитику для всех постов
            analytics_query = select(PostAnalytics).where(
                PostAnalytics.post_id.in_(post_ids)
            )
            analytics_result = await self.session.execute(analytics_query)
            analytics_records = analytics_result.scalars().all()

            # Агрегируем данные
            total_views = sum(record.views_count for record in analytics_records)
            total_clicks = sum(record.clicks_count for record in analytics_records)
            total_shares = sum(record.shares_count for record in analytics_records)

            # Объединяем реакции
            total_reactions = {}
            for record in analytics_records:
                if record.reactions:
                    for reaction, count in record.reactions.items():
                        total_reactions[reaction] = (
                            total_reactions.get(reaction, 0) + count
                        )

            # Вычисляем метрики
            average_ctr = (total_clicks / total_views * 100) if total_views > 0 else 0.0
            total_reaction_count = sum(total_reactions.values())
            average_engagement = (
                (
                    (total_clicks + total_shares + total_reaction_count)
                    / total_views
                    * 100
                )
                if total_views > 0
                else 0.0
            )

            # Топ постов по просмотрам
            post_stats = {}
            for record in analytics_records:
                if record.post_id not in post_stats:
                    post_stats[record.post_id] = {
                        "views": 0,
                        "clicks": 0,
                        "shares": 0,
                        "reactions": 0,
                    }

                post_stats[record.post_id]["views"] += record.views_count
                post_stats[record.post_id]["clicks"] += record.clicks_count
                post_stats[record.post_id]["shares"] += record.shares_count
                if record.reactions:
                    post_stats[record.post_id]["reactions"] += sum(
                        record.reactions.values()
                    )

            # Сортируем посты по просмотрам
            top_posts = []
            for post in posts:
                if post.id in post_stats:
                    stats = post_stats[post.id]
                    top_posts.append(
                        {
                            "post_id": post.id,
                            "title": post.title,
                            "views": stats["views"],
                            "clicks": stats["clicks"],
                            "shares": stats["shares"],
                            "reactions": stats["reactions"],
                            "ctr": (stats["clicks"] / stats["views"] * 100)
                            if stats["views"] > 0
                            else 0.0,
                        }
                    )

            top_posts.sort(key=lambda x: x["views"], reverse=True)
            top_posts = top_posts[:10]  # Топ 10 постов

            return {
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "posts_count": len(posts),
                "total_views": total_views,
                "total_clicks": total_clicks,
                "total_shares": total_shares,
                "total_reactions": total_reactions,
                "average_ctr": round(average_ctr, 2),
                "average_engagement": round(average_engagement, 2),
                "top_posts": top_posts,
            }
        except Exception:
            return {}

    async def get_group_analytics(
        self, group_id: int, days: int = 30
    ) -> dict[str, Any]:
        """Получение аналитики по группе за период"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            # Получаем аналитику для группы
            query = select(PostAnalytics).where(
                PostAnalytics.group_id == group_id,
                PostAnalytics.created_at >= start_date,
            )
            result = await self.session.execute(query)
            analytics_records = result.scalars().all()

            if not analytics_records:
                return {
                    "group_id": group_id,
                    "period_days": days,
                    "posts_count": 0,
                    "total_views": 0,
                    "total_clicks": 0,
                    "total_shares": 0,
                    "total_reactions": {},
                    "average_ctr": 0.0,
                    "average_engagement": 0.0,
                }

            # Агрегируем данные
            total_views = sum(record.views_count for record in analytics_records)
            total_clicks = sum(record.clicks_count for record in analytics_records)
            total_shares = sum(record.shares_count for record in analytics_records)

            # Объединяем реакции
            total_reactions = {}
            for record in analytics_records:
                if record.reactions:
                    for reaction, count in record.reactions.items():
                        total_reactions[reaction] = (
                            total_reactions.get(reaction, 0) + count
                        )

            # Вычисляем метрики
            average_ctr = (total_clicks / total_views * 100) if total_views > 0 else 0.0
            total_reaction_count = sum(total_reactions.values())
            average_engagement = (
                (
                    (total_clicks + total_shares + total_reaction_count)
                    / total_views
                    * 100
                )
                if total_views > 0
                else 0.0
            )

            return {
                "group_id": group_id,
                "period_days": days,
                "posts_count": len({record.post_id for record in analytics_records}),
                "total_views": total_views,
                "total_clicks": total_clicks,
                "total_shares": total_shares,
                "total_reactions": total_reactions,
                "average_ctr": round(average_ctr, 2),
                "average_engagement": round(average_engagement, 2),
            }
        except Exception:
            return {}

    async def _get_or_create_analytics(
        self, post_id: int, group_id: int
    ) -> PostAnalytics:
        """Получение или создание записи аналитики"""
        # Ищем существующую запись
        query = select(PostAnalytics).where(
            PostAnalytics.post_id == post_id, PostAnalytics.group_id == group_id
        )
        result = await self.session.execute(query)
        analytics = result.scalar_one_or_none()

        if analytics is None:
            # Создаем новую запись
            analytics = PostAnalytics(
                post_id=post_id,
                group_id=group_id,
                views_count=0,
                clicks_count=0,
                shares_count=0,
                reactions=None,
            )
            self.session.add(analytics)
            await self.session.flush()

        return analytics

    async def delete_post_analytics(self, post_id: int) -> bool:
        """Удаление всей аналитики поста"""
        try:
            query = select(PostAnalytics).where(PostAnalytics.post_id == post_id)
            result = await self.session.execute(query)
            analytics_records = result.scalars().all()

            for record in analytics_records:
                await self.session.delete(record)

            await self.session.flush()
            return True
        except Exception:
            return False

    async def get_popular_reactions(self, days: int = 30) -> dict[str, int]:
        """Получение популярных реакций за период"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            query = select(PostAnalytics).where(
                PostAnalytics.created_at >= start_date,
                PostAnalytics.reactions.isnot(None),
            )
            result = await self.session.execute(query)
            analytics_records = result.scalars().all()

            # Агрегируем реакции
            popular_reactions = {}
            for record in analytics_records:
                if record.reactions:
                    for reaction, count in record.reactions.items():
                        popular_reactions[reaction] = (
                            popular_reactions.get(reaction, 0) + count
                        )

            # Сортируем по популярности
            return dict(
                sorted(popular_reactions.items(), key=lambda x: x[1], reverse=True)
            )
        except Exception:
            return {}
