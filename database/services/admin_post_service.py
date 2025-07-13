# database/services/admin_post_service.py

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdminPost, Poll, PostStatus, PostType, PublishedPost
from ..repository import AdminPostRepository, PollRepository, PublishedPostRepository


class AdminPostService:
    """Сервис для работы с административными постами"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.admin_post_repo = AdminPostRepository(session)
        self.poll_repo = PollRepository(session)
        self.published_post_repo = PublishedPostRepository(session)

    # Методы для работы с черновиками
    async def create_draft(
        self,
        user_id: int,
        title: str,
        content: str,
        post_type: PostType = PostType.TEXT,
        **kwargs,
    ) -> AdminPost:
        """Создание черновика поста"""
        return await self.admin_post_repo.create(
            user_id=user_id,
            title=title,
            content=content,
            post_type=post_type,
            status=PostStatus.DRAFT,
            **kwargs,
        )

    async def update_draft(self, post_id: int, **kwargs) -> AdminPost | None:
        """Обновление черновика поста"""
        post = await self.admin_post_repo.get_by_id(post_id)
        if not post or post.status != PostStatus.DRAFT:
            return None

        return await self.admin_post_repo.update(post, **kwargs)

    async def get_drafts(self, user_id: int) -> list[AdminPost]:
        """Получение всех черновиков пользователя"""
        return await self.admin_post_repo.get_by_user_and_status(
            user_id, PostStatus.DRAFT
        )

    async def delete_draft(self, post_id: int, user_id: int) -> bool:
        """Удаление черновика"""
        post = await self.admin_post_repo.get_by_id(post_id)
        if not post or post.user_id != user_id or post.status != PostStatus.DRAFT:
            return False

        await self.admin_post_repo.delete(post)
        return True

    # Методы для публикации
    async def publish_post(
        self,
        post_id: int,
        target_groups: list[int],
        scheduled_at: datetime | None = None,
    ) -> AdminPost | None:
        """Публикация поста"""
        post = await self.admin_post_repo.get_by_id(post_id)
        if not post:
            return None

        # Обновляем статус и целевые группы
        status = PostStatus.SCHEDULED if scheduled_at else PostStatus.PUBLISHED
        update_data = {
            "status": status,
            "target_groups": target_groups,
            "published_at": datetime.now() if not scheduled_at else None,
            "scheduled_at": scheduled_at,
        }

        return await self.admin_post_repo.update(post, **update_data)

    async def schedule_post(
        self, post_id: int, scheduled_at: datetime, target_groups: list[int]
    ) -> AdminPost | None:
        """Планирование поста на определенное время"""
        return await self.publish_post(post_id, target_groups, scheduled_at)

    async def get_scheduled_posts(self) -> list[AdminPost]:
        """Получение всех запланированных постов"""
        return await self.admin_post_repo.get_by_status(PostStatus.SCHEDULED)

    async def get_ready_to_publish(self) -> list[AdminPost]:
        """Получение постов готовых к публикации (время пришло)"""
        return await self.admin_post_repo.get_ready_to_publish()

    # Методы для отмены
    async def cancel_post(self, post_id: int, reason: str = None) -> AdminPost | None:
        """Отмена поста (перевод в статус CANCELLED)"""
        post = await self.admin_post_repo.get_by_id(post_id)
        if not post or post.status in [PostStatus.PUBLISHED, PostStatus.CANCELLED]:
            return None

        update_data = {"status": PostStatus.CANCELLED}
        if reason:
            update_data["error_message"] = f"Отменено: {reason}"

        return await self.admin_post_repo.update(post, **update_data)

    async def mark_as_error(self, post_id: int, error_message: str) -> AdminPost | None:
        """Отметка поста как ошибочного"""
        post = await self.admin_post_repo.get_by_id(post_id)
        if not post:
            return None

        return await self.admin_post_repo.update(
            post, status=PostStatus.ERROR, error_message=error_message
        )

    # Методы для работы с опросами
    async def create_poll_post(
        self,
        user_id: int,
        title: str,
        question: str,
        options: list[str],
        poll_type: str = "regular",
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
        **kwargs,
    ) -> AdminPost:
        """Создание поста с опросом"""
        # Создаем пост
        post = await self.create_draft(
            user_id=user_id,
            title=title,
            content=question,
            post_type=PostType.POLL,
            **kwargs,
        )

        # Создаем опрос
        poll = await self.poll_repo.create(
            post_id=post.id,
            question=question,
            poll_type=poll_type,
            is_anonymous=is_anonymous,
            allows_multiple_answers=allows_multiple_answers,
        )

        # Создаем варианты ответов
        for i, option_text in enumerate(options):
            await self.poll_repo.create_option(
                poll_id=poll.id, text=option_text, position=i
            )

        return post

    async def update_poll(
        self, post_id: int, question: str = None, options: list[str] = None, **kwargs
    ) -> Poll | None:
        """Обновление опроса"""
        post = await self.admin_post_repo.get_by_id(post_id)
        if not post or post.post_type != PostType.POLL:
            return None

        poll = await self.poll_repo.get_by_post_id(post_id)
        if not poll:
            return None

        # Обновляем опрос
        update_data = {}
        if question:
            update_data["question"] = question
        update_data.update(kwargs)

        poll = await self.poll_repo.update(poll, **update_data)

        # Обновляем варианты ответов если переданы
        if options:
            await self.poll_repo.delete_options(poll.id)
            for i, option_text in enumerate(options):
                await self.poll_repo.create_option(
                    poll_id=poll.id, text=option_text, position=i
                )

        return poll

    # Методы для работы с опубликованными постами
    async def add_published_post(
        self, post_id: int, chat_id: int, message_id: int
    ) -> PublishedPost:
        """Добавление информации об опубликованном посте"""
        return await self.published_post_repo.create(
            post_id=post_id, chat_id=chat_id, message_id=message_id
        )

    async def get_published_posts(self, post_id: int) -> list[PublishedPost]:
        """Получение всех публикаций поста"""
        return await self.published_post_repo.get_by_post_id(post_id)

    async def delete_published_post(self, post_id: int, chat_id: int) -> bool:
        """Удаление информации об опубликованном посте"""
        published_post = await self.published_post_repo.get_by_post_and_chat(
            post_id, chat_id
        )
        if not published_post:
            return False

        await self.published_post_repo.delete(published_post)
        return True

    # Общие методы
    async def get_post(self, post_id: int) -> AdminPost | None:
        """Получение поста по ID с загрузкой связанных данных"""
        return await self.admin_post_repo.get_with_relations(post_id)

    async def get_user_posts(
        self, user_id: int, status: PostStatus = None
    ) -> list[AdminPost]:
        """Получение всех постов пользователя"""
        if status:
            return await self.admin_post_repo.get_by_user_and_status(user_id, status)
        return await self.admin_post_repo.get_by_user_id(user_id)

    async def get_posts_by_status(self, status: PostStatus) -> list[AdminPost]:
        """Получение всех постов по статусу"""
        return await self.admin_post_repo.get_by_status(status)

    async def get_posts_with_errors(self) -> list[AdminPost]:
        """Получение всех постов с ошибками"""
        return await self.admin_post_repo.get_by_status(PostStatus.ERROR)

    async def search_posts(
        self, query: str, user_id: int = None, status: PostStatus = None
    ) -> list[AdminPost]:
        """Поиск постов по заголовку или содержимому"""
        return await self.admin_post_repo.search_posts(query, user_id, status)

    async def get_analytics_data(self, post_id: int) -> dict:
        """Получение аналитических данных поста"""
        post = await self.admin_post_repo.get_with_analytics(post_id)
        if not post or not post.analytics:
            return {}

        analytics = post.analytics
        return {
            "views": analytics.views,
            "clicks": analytics.clicks,
            "shares": analytics.shares,
            "reactions": analytics.reactions,
            "engagement_rate": analytics.engagement_rate,
            "reach": analytics.reach,
        }
