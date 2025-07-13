# database/services/__init__.py

# Импортируем все сервисы для обеспечения обратной совместимости
from .ad_analytics_service import AdAnalyticsService
from .ad_campaign_service import AdCampaignService
from .ad_creative_service import AdCreativeService
from .ad_placement_service import AdPlacementService
from .admin_post_service import AdminPostService
from .advertiser_service import AdvertiserService
from .captcha_service import CaptchaService
from .filter_service import FilterService
from .group_service import GroupService
from .notification_service import NotificationService
from .poll_service import PollService
from .post_analytics_service import PostAnalyticsService
from .scheduler_service import SchedulerService
from .template_service import TemplateService
from .user_service import UserService


# Экспортируем все сервисы для обеспечения обратной совместимости
__all__ = [
    "UserService",
    "GroupService",
    "FilterService",
    "CaptchaService",
    "AdvertiserService",
    "AdCampaignService",
    "AdCreativeService",
    "AdPlacementService",
    "AdAnalyticsService",
    "AdminPostService",
    "PollService",
    "NotificationService",
    "PostAnalyticsService",
    "SchedulerService",
    "TemplateService",
]
