# database/repository.py
"""
Repository Pattern - базовые CRUD операции и репозитории для всех моделей
"""

from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, joinedload

from .models import (
    AdAnalytics,
    AdCampaign,
    AdCampaignStatus,
    AdCreative,
    AdCreativeStatus,
    AdminPost,
    AdPlacement,
    Advertiser,
    CaptchaSession,
    CaptchaSetting,
    FilterRule,
    Group,
    GroupMember,
    MemberStatus,
    Poll,
    PollOption,
    PostStatus,
    PublishedPost,
    Transaction,
    User,
)


T = TypeVar("T", bound=DeclarativeBase)


class BaseRepository(ABC, Generic[T]):  # noqa: UP046
    """Базовый репозиторий - только CRUD операции"""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: Any) -> T | None:  # noqa: A002
        """Получение по ID"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many(self, ids: list[Any]) -> list[T]:
        """Получение нескольких записей по ID"""
        stmt = select(self.model_class).where(self.model_class.id.in_(ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs) -> T:
        """Создание новой записи"""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: T, **kwargs) -> T:
        """Обновление существующей записи"""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        """Удаление записи"""
        self.session.delete(instance)
        await self.session.flush()

    async def get_all(self) -> list[T]:
        """Получение всех записей"""
        stmt = select(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalars().all()


# Репозитории для основных моделей
class FilterRuleRepository(BaseRepository[FilterRule]):
    """Репозиторий для работы с правилами фильтров"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, FilterRule)

    async def get_by_group_id(self, group_id: int) -> FilterRule | None:
        """Получение правил фильтра по ID группы"""
        stmt = select(FilterRule).where(FilterRule.id == group_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_column_name(
        self, group_id: int, column_name: str, value: Any
    ) -> bool:
        """Обновление правила фильтра по названию колонки в группе"""
        if not hasattr(FilterRule, column_name):
            return False

        stmt = (
            update(FilterRule)
            .where(FilterRule.id == group_id)
            .values({column_name: value})
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class UserRepository(BaseRepository[User]):
    """Репозиторий пользователей - расширенные CRUD операции"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_user_by_filters(self, filters: dict) -> User | None:
        """Получение пользователя по фильтрам"""
        stmt = select(User).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class GroupRepository(BaseRepository[Group]):
    """Репозиторий для работы с группами"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Group)


class GroupMemberRepository(BaseRepository[GroupMember]):
    """Репозиторий участников групп"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, GroupMember)

    async def get_by_user_and_group(
        self, user_id: int, group_id: int
    ) -> GroupMember | None:
        """Получение членства по пользователю и группе"""
        stmt = select(GroupMember).where(
            and_(GroupMember.user_id == user_id, GroupMember.group_id == group_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_group_members(
        self, group_id: int, status: MemberStatus | None = None
    ) -> list[GroupMember]:
        """Получение участников группы"""
        stmt = select(GroupMember).options(joinedload(GroupMember.user))

        conditions = [GroupMember.group_id == group_id]
        if status:
            conditions.append(GroupMember.status == status)

        stmt = stmt.where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()


class CaptchaSettingRepository(BaseRepository[CaptchaSetting]):
    """Репозиторий для работы с настройками каптчи"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CaptchaSetting)

    async def get_by_group_id(self, group_id: int) -> CaptchaSetting | None:
        """Получение настроек каптчи по ID группы"""
        stmt = select(CaptchaSetting).where(CaptchaSetting.group_id == group_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_column_name(
        self, group_id: int, column_name: str, value: Any
    ) -> bool:
        """Обновление настройки каптчи по названию колонки в группе"""
        if not hasattr(CaptchaSetting, column_name):
            return False

        stmt = (
            update(CaptchaSetting)
            .where(CaptchaSetting.group_id == group_id)
            .values({column_name: value})
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class CaptchaSessionRepository(BaseRepository[CaptchaSession]):
    """Репозиторий для работы с сессиями каптчи"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CaptchaSession)

    async def get_by_user_and_group(
        self, user_id: int, group_id: int
    ) -> CaptchaSession | None:
        """Получение активной сессии каптчи по пользователю и группе"""
        stmt = select(CaptchaSession).where(
            and_(
                CaptchaSession.user_id == user_id,
                CaptchaSession.group_id == group_id,
                CaptchaSession.status == "pending",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_sessions_by_group(self, group_id: int) -> list[CaptchaSession]:
        """Получение всех активных сессий каптчи в группе"""
        stmt = select(CaptchaSession).where(
            and_(
                CaptchaSession.group_id == group_id,
                CaptchaSession.status == "pending",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def cleanup_expired_sessions(self) -> int:
        """Очистка истекших сессий каптчи"""
        from datetime import datetime

        stmt = (
            update(CaptchaSession)
            .where(
                and_(
                    CaptchaSession.status == "pending",
                    CaptchaSession.expires_at < datetime.now(),
                )
            )
            .values(status="expired")
        )
        result = await self.session.execute(stmt)
        return result.rowcount


# Репозитории для рекламной системы
class AdvertiserRepository(BaseRepository[Advertiser]):
    """Репозиторий для работы с рекламодателями"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Advertiser)

    async def get_by_user_id(self, user_id: int) -> Advertiser | None:
        """Получение рекламодателя по ID пользователя"""
        stmt = select(Advertiser).where(Advertiser.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_campaigns(self, advertiser_id: int) -> Advertiser | None:
        """Получение рекламодателя с его кампаниями"""
        stmt = (
            select(Advertiser)
            .options(joinedload(Advertiser.ad_campaigns))
            .where(Advertiser.id == advertiser_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AdCampaignRepository(BaseRepository[AdCampaign]):
    """Репозиторий для работы с рекламными кампаниями"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AdCampaign)

    async def get_by_advertiser(self, advertiser_id: int) -> list[AdCampaign]:
        """Получение всех кампаний рекламодателя"""
        stmt = select(AdCampaign).where(AdCampaign.advertiser_id == advertiser_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_campaigns(self) -> list[AdCampaign]:
        """Получение всех активных кампаний"""
        stmt = select(AdCampaign).where(AdCampaign.status == AdCampaignStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_creatives(self, campaign_id: int) -> AdCampaign | None:
        """Получение кампании с её креативами"""
        stmt = (
            select(AdCampaign)
            .options(joinedload(AdCampaign.ad_creatives))
            .where(AdCampaign.id == campaign_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_placements(self, campaign_id: int) -> AdCampaign | None:
        """Получение кампании с местами размещения"""
        stmt = (
            select(AdCampaign)
            .options(joinedload(AdCampaign.ad_placements))
            .where(AdCampaign.id == campaign_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AdCreativeRepository(BaseRepository[AdCreative]):
    """Репозиторий для работы с рекламными креативами"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AdCreative)

    async def get_by_campaign(self, campaign_id: int) -> list[AdCreative]:
        """Получение всех креативов кампании"""
        stmt = select(AdCreative).where(AdCreative.campaign_id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_moderation(self) -> list[AdCreative]:
        """Получение всех креативов, ожидающих модерации"""
        stmt = select(AdCreative).where(AdCreative.status == AdCreativeStatus.PENDING)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class AdPlacementRepository(BaseRepository[AdPlacement]):
    """Репозиторий для работы с местами размещения рекламы"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AdPlacement)

    async def get_by_campaign(self, campaign_id: int) -> list[AdPlacement]:
        """Получение всех мест размещения кампании"""
        stmt = select(AdPlacement).where(AdPlacement.campaign_id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_group(self, group_id: int) -> list[AdPlacement]:
        """Получение всех размещений в группе"""
        stmt = select(AdPlacement).where(AdPlacement.group_id == group_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_campaign_and_group(
        self, placement_id: int
    ) -> AdPlacement | None:
        """Получение размещения с кампанией и группой"""
        stmt = (
            select(AdPlacement)
            .options(
                joinedload(AdPlacement.ad_campaign),
                joinedload(AdPlacement.group),
            )
            .where(AdPlacement.id == placement_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AdAnalyticsRepository(BaseRepository[AdAnalytics]):
    """Репозиторий для работы с аналитикой рекламы"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AdAnalytics)

    async def get_by_creative(self, creative_id: int) -> list[AdAnalytics]:
        """Получение всех событий аналитики для креатива"""
        stmt = select(AdAnalytics).where(AdAnalytics.creative_id == creative_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_group(self, group_id: int) -> list[AdAnalytics]:
        """Получение всех событий аналитики для группы"""
        stmt = select(AdAnalytics).where(AdAnalytics.group_id == group_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, user_id: int) -> list[AdAnalytics]:
        """Получение всех событий аналитики для пользователя"""
        stmt = select(AdAnalytics).where(AdAnalytics.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TransactionRepository(BaseRepository[Transaction]):
    """Репозиторий для работы с транзакциями"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Transaction)

    async def get_by_advertiser(self, advertiser_id: int) -> list[Transaction]:
        """Получение всех транзакций рекламодателя"""
        stmt = select(Transaction).where(Transaction.advertiser_id == advertiser_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


# Репозитории для системы постов
class AdminPostRepository(BaseRepository[AdminPost]):
    """Репозиторий для работы с административными постами"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AdminPost)

    async def get_by_user_id(self, user_id: int) -> list[AdminPost]:
        """Получение всех постов пользователя"""
        stmt = select(AdminPost).where(AdminPost.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(self, status: PostStatus) -> list[AdminPost]:
        """Получение всех постов по статусу"""
        stmt = select(AdminPost).where(AdminPost.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user_and_status(
        self, user_id: int, status: PostStatus
    ) -> list[AdminPost]:
        """Получение постов пользователя по статусу"""
        stmt = select(AdminPost).where(
            and_(AdminPost.user_id == user_id, AdminPost.status == status)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ready_to_publish(self) -> list[AdminPost]:
        """Получение постов готовых к публикации"""
        from datetime import datetime

        stmt = select(AdminPost).where(
            and_(
                AdminPost.status == PostStatus.SCHEDULED,
                AdminPost.scheduled_at <= datetime.now(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_relations(self, post_id: int) -> AdminPost | None:
        """Получение поста с загрузкой связанных данных"""
        stmt = (
            select(AdminPost)
            .options(
                joinedload(AdminPost.poll).joinedload(Poll.options),
                joinedload(AdminPost.published_posts),
                joinedload(AdminPost.analytics),
            )
            .where(AdminPost.id == post_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_analytics(self, post_id: int) -> AdminPost | None:
        """Получение поста с аналитикой"""
        stmt = (
            select(AdminPost)
            .options(joinedload(AdminPost.analytics))
            .where(AdminPost.id == post_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_posts(
        self, query: str, user_id: int = None, status: PostStatus = None
    ) -> list[AdminPost]:
        """Поиск постов по заголовку или содержимому"""
        conditions = [
            AdminPost.title.ilike(f"%{query}%") | AdminPost.content.ilike(f"%{query}%")
        ]

        if user_id:
            conditions.append(AdminPost.user_id == user_id)
        if status:
            conditions.append(AdminPost.status == status)

        stmt = select(AdminPost).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PollRepository(BaseRepository[Poll]):
    """Репозиторий для работы с опросами"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Poll)

    async def get_by_post_id(self, post_id: int) -> Poll | None:
        """Получение опроса по ID поста"""
        stmt = (
            select(Poll)
            .options(joinedload(Poll.options))
            .where(Poll.post_id == post_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_option(self, poll_id: int, text: str, position: int) -> PollOption:
        """Создание варианта ответа для опроса"""
        option = PollOption(poll_id=poll_id, text=text, position=position)
        self.session.add(option)
        await self.session.flush()
        return option

    async def delete_options(self, poll_id: int) -> None:
        """Удаление всех вариантов ответов опроса"""
        stmt = select(PollOption).where(PollOption.poll_id == poll_id)
        result = await self.session.execute(stmt)
        options = result.scalars().all()
        for option in options:
            await self.session.delete(option)
        await self.session.flush()

    async def get_with_votes(self, poll_id: int) -> Poll | None:
        """Получение опроса с голосами"""
        stmt = (
            select(Poll)
            .options(
                joinedload(Poll.options),
                joinedload(Poll.votes),
            )
            .where(Poll.id == poll_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class PublishedPostRepository(BaseRepository[PublishedPost]):
    """Репозиторий для работы с опубликованными постами"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PublishedPost)

    async def get_by_post_id(self, post_id: int) -> list[PublishedPost]:
        """Получение всех публикаций поста"""
        stmt = select(PublishedPost).where(PublishedPost.post_id == post_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_post_and_chat(
        self, post_id: int, chat_id: int
    ) -> PublishedPost | None:
        """Получение публикации поста в конкретном чате"""
        stmt = select(PublishedPost).where(
            and_(
                PublishedPost.post_id == post_id,
                PublishedPost.chat_id == chat_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_chat_id(self, chat_id: int) -> list[PublishedPost]:
        """Получение всех публикаций в чате"""
        stmt = select(PublishedPost).where(PublishedPost.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
