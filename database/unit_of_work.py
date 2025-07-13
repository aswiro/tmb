# database/unit_of_work.py
"""
Unit of Work Pattern для управления транзакциями
"""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from .analytics import (
    AdvertiserAnalytics,
    CampaignAnalytics,
    GroupAdAnalytics,
    GroupAnalytics,
    UserAnalytics,
)
from .repository import (
    AdAnalyticsRepository,
    AdCampaignRepository,
    AdCreativeRepository,
    AdminPostRepository,
    AdPlacementRepository,
    AdvertiserRepository,
    CaptchaSessionRepository,
    CaptchaSettingRepository,
    FilterRuleRepository,
    GroupMemberRepository,
    GroupRepository,
    PollRepository,
    PublishedPostRepository,
    TransactionRepository,
    UserRepository,
)
from .services import (
    AdAnalyticsService,
    AdCampaignService,
    AdCreativeService,
    AdminPostService,
    AdPlacementService,
    AdvertiserService,
    CaptchaService,
    FilterService,
    GroupService,
    NotificationService,
    PollService,
    PostAnalyticsService,
    SchedulerService,
    TemplateService,
    UserService,
)


class UnitOfWork:
    """Unit of Work для управления транзакциями"""

    def __init__(self, session: AsyncSession):
        self.session = session

        # Repositories
        self.users = UserRepository(session)
        self.group_members = GroupMemberRepository(session)
        self.groups = GroupRepository(session)
        self.filter_rules = FilterRuleRepository(session)
        self.captcha_settings = CaptchaSettingRepository(session)
        self.captcha_sessions = CaptchaSessionRepository(session)

        # Ad System Repositories
        self.advertisers = AdvertiserRepository(session)
        self.ad_campaigns = AdCampaignRepository(session)
        self.ad_creatives = AdCreativeRepository(session)
        self.ad_placements = AdPlacementRepository(session)
        self.ad_analytics = AdAnalyticsRepository(session)
        self.transactions = TransactionRepository(session)

        # Post System Repositories
        self.admin_posts = AdminPostRepository(session)
        self.polls = PollRepository(session)
        self.published_posts = PublishedPostRepository(session)

        # Services
        self.user_service = UserService(session)
        self.group_service = GroupService(session)
        self.filter_service = FilterService(session)
        self.captcha_service = CaptchaService(session)
        self.notification_service = NotificationService(session)
        self.template_service = TemplateService(session, self.repository)

        # Ad System Services
        self.advertiser_service = AdvertiserService(session)
        self.ad_campaign_service = AdCampaignService(session)
        self.ad_creative_service = AdCreativeService(session)
        self.ad_placement_service = AdPlacementService(session)
        self.ad_analytics_service = AdAnalyticsService(session)

        # Post System Services
        self.admin_post_service = AdminPostService(session)
        self.poll_service = PollService(session)
        self.scheduler_service = SchedulerService(session)
        self.post_analytics_service = PostAnalyticsService(session)

        # Analytics
        self.user_analytics = UserAnalytics(session)
        self.group_analytics = GroupAnalytics(session)

        # Ad System Analytics
        self.advertiser_analytics = AdvertiserAnalytics(session)
        self.campaign_analytics = CampaignAnalytics(session)
        self.group_ad_analytics = GroupAdAnalytics(session)

    async def commit(self):
        """Коммит транзакции"""
        await self.session.commit()

    async def rollback(self):
        """Откат транзакции"""
        await self.session.rollback()

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


# Пример использования без дублирования
"""
# В обработчике команды Telegram бота
async def start_handler(message, bot):
    async with database.get_session() as session:
        uow = UnitOfWork(session)

        # Используем сервис для бизнес-логики
        user = await uow.user_service.create_or_update_user(message.from_user)

        # Используем аналитику для отчетов
        stats = await uow.user_analytics.get_user_growth_stats(days=7)

        await message.reply(
            f"Привет, {user.full_name}!\n"
            f"Новых пользователей за неделю: {stats['new_users']}"
        )

# Обработка приглашения
async def process_referral(inviter_id: int, invited_id: int):
    async with database.get_session() as session:
        async with UnitOfWork(session) as uow:
            # Все операции в одной транзакции
            success = await uow.user_service.process_invitation(inviter_id, invited_id)
            if success:
                await uow.commit()
                return True
            else:
                await uow.rollback()
                return False
"""
