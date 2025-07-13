# database/services/scheduler_service.py

from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdminPost, PostStatus
from ..repository import AdminPostRepository
from .admin_post_service import AdminPostService


class SchedulerService:
    """Сервис для планирования и автоматической публикации постов"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.admin_post_repo = AdminPostRepository(session)
        self.admin_post_service = AdminPostService(session)

    async def check_scheduled_posts(self) -> None:
        """Проверка и публикация запланированных постов"""
        try:
            # Получаем посты готовые к публикации
            ready_posts = await self.admin_post_repo.get_ready_to_publish()

            logger.info(f"Found {len(ready_posts)} posts ready to publish")

            for post in ready_posts:
                success = await self.publish_scheduled_post(post)
                if success:
                    logger.info(f"Successfully published post {post.id}")
                else:
                    logger.error(f"Failed to publish post {post.id}")

        except Exception as e:
            logger.error(f"Error checking scheduled posts: {e}")

    async def publish_scheduled_post(self, post: AdminPost) -> bool:
        """Публикация запланированного поста"""
        try:
            # Обновляем статус поста на PUBLISHED
            await self.admin_post_repo.update(
                post, status=PostStatus.PUBLISHED, published_at=datetime.now()
            )

            # Здесь будет логика отправки поста в Telegram группы
            # TODO: Интеграция с Telegram Bot API для отправки сообщений

            return True

        except Exception as e:
            logger.error(f"Error publishing scheduled post {post.id}: {e}")

            # Отмечаем пост как ошибочный
            await self.admin_post_service.mark_as_error(
                post.id, f"Ошибка публикации: {str(e)}"
            )

            return False

    async def expire_posts(self) -> None:
        """Обработка истекших постов"""
        try:
            # Получаем все запланированные посты
            scheduled_posts = await self.admin_post_repo.get_by_status(
                PostStatus.SCHEDULED
            )

            current_time = datetime.now()
            expired_count = 0

            for post in scheduled_posts:
                # Проверяем, не истек ли срок публикации (например, больше 24 часов)
                if (
                    post.scheduled_at
                    and (current_time - post.scheduled_at).total_seconds() > 86400
                ):  # 24 часа
                    await self.admin_post_service.cancel_post(
                        post.id, "Срок публикации истек"
                    )
                    expired_count += 1

            if expired_count > 0:
                logger.info(f"Expired {expired_count} posts")

        except Exception as e:
            logger.error(f"Error expiring posts: {e}")

    async def get_next_scheduled_posts(self, limit: int = 10) -> list[AdminPost]:
        """Получение следующих запланированных постов"""
        try:
            scheduled_posts = await self.admin_post_repo.get_by_status(
                PostStatus.SCHEDULED
            )

            # Сортируем по времени публикации и берем первые limit постов
            sorted_posts = sorted(
                [post for post in scheduled_posts if post.scheduled_at],
                key=lambda x: x.scheduled_at,
            )

            return sorted_posts[:limit]

        except Exception as e:
            logger.error(f"Error getting next scheduled posts: {e}")
            return []

    async def reschedule_post(
        self, post_id: int, new_scheduled_at: datetime
    ) -> AdminPost | None:
        """Перепланирование поста на новое время"""
        try:
            post = await self.admin_post_repo.get_by_id(post_id)

            if not post or post.status != PostStatus.SCHEDULED:
                logger.warning(f"Post {post_id} not found or not scheduled")
                return None

            # Обновляем время публикации
            updated_post = await self.admin_post_repo.update(
                post, scheduled_at=new_scheduled_at
            )

            logger.info(f"Rescheduled post {post_id} to {new_scheduled_at}")
            return updated_post

        except Exception as e:
            logger.error(f"Error rescheduling post {post_id}: {e}")
            return None

    async def get_scheduler_stats(self) -> dict:
        """Получение статистики планировщика"""
        try:
            scheduled_posts = await self.admin_post_repo.get_by_status(
                PostStatus.SCHEDULED
            )
            published_posts = await self.admin_post_repo.get_by_status(
                PostStatus.PUBLISHED
            )
            error_posts = await self.admin_post_repo.get_by_status(PostStatus.ERROR)

            # Подсчитываем посты готовые к публикации
            ready_posts = await self.admin_post_repo.get_ready_to_publish()

            return {
                "scheduled_count": len(scheduled_posts),
                "published_count": len(published_posts),
                "error_count": len(error_posts),
                "ready_to_publish": len(ready_posts),
            }

        except Exception as e:
            logger.error(f"Error getting scheduler stats: {e}")
            return {
                "scheduled_count": 0,
                "published_count": 0,
                "error_count": 0,
                "ready_to_publish": 0,
            }
