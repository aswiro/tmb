from datetime import datetime
from enum import Enum
from typing import Any

from config.logger import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.admin_post import AdminPost
from database.models.user import User
from database.repository import (
    AdminPostRepository,
    PublishedPostRepository,
    UserRepository,
)


class NotificationType(Enum):
    """Типы уведомлений"""

    POST_PUBLISHED = "post_published"
    POST_FAILED = "post_failed"
    POST_SCHEDULED = "post_scheduled"
    POST_CANCELLED = "post_cancelled"
    SYSTEM_ERROR = "system_error"
    MODERATION_REQUIRED = "moderation_required"
    QUOTA_WARNING = "quota_warning"
    PERFORMANCE_ALERT = "performance_alert"


class NotificationPriority(Enum):
    """Приоритеты уведомлений"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Каналы доставки уведомлений"""

    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationService:
    """Сервис для управления уведомлениями админов"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.admin_post_repo = AdminPostRepository(session)
        self.user_repo = UserRepository(session)
        self.published_post_repo = PublishedPostRepository(session)

        # Настройки уведомлений по умолчанию
        self.default_channels = [NotificationChannel.TELEGRAM]
        self.notification_settings = {
            NotificationType.POST_PUBLISHED: {
                "priority": NotificationPriority.MEDIUM,
                "channels": [NotificationChannel.TELEGRAM, NotificationChannel.IN_APP],
            },
            NotificationType.POST_FAILED: {
                "priority": NotificationPriority.HIGH,
                "channels": [NotificationChannel.TELEGRAM, NotificationChannel.EMAIL],
            },
            NotificationType.SYSTEM_ERROR: {
                "priority": NotificationPriority.CRITICAL,
                "channels": [
                    NotificationChannel.TELEGRAM,
                    NotificationChannel.EMAIL,
                    NotificationChannel.WEBHOOK,
                ],
            },
            NotificationType.MODERATION_REQUIRED: {
                "priority": NotificationPriority.HIGH,
                "channels": [NotificationChannel.TELEGRAM],
            },
        }

    async def notify_post_published(
        self, post_id: int, admin_id: int | None = None
    ) -> bool:
        """Уведомление о успешной публикации поста"""
        try:
            post = await self.admin_post_repo.get_by_id(post_id)
            if not post:
                logger.error(f"Post {post_id} not found for notification")
                return False

            message = self._format_post_published_message(post)

            # Определяем получателей
            recipients = await self._get_notification_recipients(
                NotificationType.POST_PUBLISHED, admin_id or post.author_id
            )

            # Отправляем уведомления
            success = await self._send_notifications(
                NotificationType.POST_PUBLISHED,
                message,
                recipients,
                metadata={"post_id": post_id},
            )

            if success:
                logger.info(f"Post published notification sent for post {post_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending post published notification: {e}")
            return False

    async def notify_post_failed(
        self, post_id: int, error_message: str, admin_id: int | None = None
    ) -> bool:
        """Уведомление об ошибке публикации поста"""
        try:
            post = await self.admin_post_repo.get_by_id(post_id)
            if not post:
                logger.error(f"Post {post_id} not found for error notification")
                return False

            message = self._format_post_failed_message(post, error_message)

            recipients = await self._get_notification_recipients(
                NotificationType.POST_FAILED, admin_id or post.author_id
            )

            success = await self._send_notifications(
                NotificationType.POST_FAILED,
                message,
                recipients,
                metadata={"post_id": post_id, "error": error_message},
            )

            if success:
                logger.info(f"Post failed notification sent for post {post_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending post failed notification: {e}")
            return False

    async def notify_post_scheduled(
        self, post_id: int, scheduled_time: datetime, admin_id: int | None = None
    ) -> bool:
        """Уведомление о запланированной публикации"""
        try:
            post = await self.admin_post_repo.get_by_id(post_id)
            if not post:
                return False

            message = self._format_post_scheduled_message(post, scheduled_time)

            recipients = await self._get_notification_recipients(
                NotificationType.POST_SCHEDULED, admin_id or post.author_id
            )

            success = await self._send_notifications(
                NotificationType.POST_SCHEDULED,
                message,
                recipients,
                metadata={
                    "post_id": post_id,
                    "scheduled_time": scheduled_time.isoformat(),
                },
            )

            return success

        except Exception as e:
            logger.error(f"Error sending post scheduled notification: {e}")
            return False

    async def notify_system_error(
        self, error_type: str, error_message: str, context: dict[str, Any] | None = None
    ) -> bool:
        """Уведомление о системной ошибке"""
        try:
            message = self._format_system_error_message(
                error_type, error_message, context
            )

            # Системные ошибки отправляются всем админам
            recipients = await self._get_all_admin_recipients()

            success = await self._send_notifications(
                NotificationType.SYSTEM_ERROR,
                message,
                recipients,
                metadata={
                    "error_type": error_type,
                    "error_message": error_message,
                    "context": context or {},
                },
            )

            if success:
                logger.info(f"System error notification sent: {error_type}")

            return success

        except Exception as e:
            logger.error(f"Error sending system error notification: {e}")
            return False

    async def notify_moderation_required(self, post_id: int, reason: str) -> bool:
        """Уведомление о необходимости модерации"""
        try:
            post = await self.admin_post_repo.get_by_id(post_id)
            if not post:
                return False

            message = self._format_moderation_required_message(post, reason)

            # Модерация - уведомляем всех админов
            recipients = await self._get_all_admin_recipients()

            success = await self._send_notifications(
                NotificationType.MODERATION_REQUIRED,
                message,
                recipients,
                metadata={"post_id": post_id, "reason": reason},
            )

            return success

        except Exception as e:
            logger.error(f"Error sending moderation notification: {e}")
            return False

    async def notify_quota_warning(
        self,
        quota_type: str,
        current_usage: int,
        limit: int,
        admin_id: int | None = None,
    ) -> bool:
        """Уведомление о превышении квот"""
        try:
            message = self._format_quota_warning_message(
                quota_type, current_usage, limit
            )

            recipients = await self._get_notification_recipients(
                NotificationType.QUOTA_WARNING, admin_id
            )

            success = await self._send_notifications(
                NotificationType.QUOTA_WARNING,
                message,
                recipients,
                metadata={
                    "quota_type": quota_type,
                    "current_usage": current_usage,
                    "limit": limit,
                },
            )

            return success

        except Exception as e:
            logger.error(f"Error sending quota warning notification: {e}")
            return False

    async def send_bulk_notification(
        self,
        notification_type: NotificationType,
        message: str,
        admin_ids: list[int],
        metadata: dict[str, Any] | None = None,
    ) -> dict[int, bool]:
        """Массовая отправка уведомлений"""
        results = {}

        for admin_id in admin_ids:
            try:
                recipients = await self._get_notification_recipients(
                    notification_type, admin_id
                )
                success = await self._send_notifications(
                    notification_type, message, recipients, metadata
                )
                results[admin_id] = success

            except Exception as e:
                logger.error(
                    f"Error sending bulk notification to admin {admin_id}: {e}"
                )
                results[admin_id] = False

        return results

    async def get_notification_history(
        self,
        admin_id: int | None = None,
        notification_type: NotificationType | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Получение истории уведомлений"""
        # В реальной реализации здесь был бы запрос к таблице уведомлений
        # Пока возвращаем заглушку
        return []

    async def update_notification_settings(
        self, admin_id: int, settings: dict[str, Any]
    ) -> bool:
        """Обновление настроек уведомлений для админа"""
        try:
            # В реальной реализации здесь было бы сохранение в БД
            logger.info(f"Notification settings updated for admin {admin_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            return False

    async def get_notification_settings(self, admin_id: int) -> dict[str, Any]:
        """Получение настроек уведомлений админа"""
        # В реальной реализации здесь был бы запрос к БД
        return self.notification_settings

    # Приватные методы для форматирования сообщений

    def _format_post_published_message(self, post: AdminPost) -> str:
        """Форматирование сообщения о публикации поста"""
        return (
            f"✅ Пост успешно опубликован\n\n"
            f"📝 Заголовок: {post.title}\n"
            f"🆔 ID поста: {post.id}\n"
            f"⏰ Время публикации: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

    def _format_post_failed_message(self, post: AdminPost, error: str) -> str:
        """Форматирование сообщения об ошибке публикации"""
        return (
            f"❌ Ошибка публикации поста\n\n"
            f"📝 Заголовок: {post.title}\n"
            f"🆔 ID поста: {post.id}\n"
            f"❗ Ошибка: {error}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

    def _format_post_scheduled_message(
        self, post: AdminPost, scheduled_time: datetime
    ) -> str:
        """Форматирование сообщения о запланированной публикации"""
        return (
            f"📅 Пост запланирован к публикации\n\n"
            f"📝 Заголовок: {post.title}\n"
            f"🆔 ID поста: {post.id}\n"
            f"⏰ Время публикации: {scheduled_time.strftime('%d.%m.%Y %H:%M')}"
        )

    def _format_system_error_message(
        self, error_type: str, error_message: str, context: dict[str, Any] | None
    ) -> str:
        """Форматирование сообщения о системной ошибке"""
        message = (
            f"🚨 Системная ошибка\n\n"
            f"🔴 Тип: {error_type}\n"
            f"📄 Сообщение: {error_message}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        if context:
            message += "\n\n📋 Контекст:\n"
            for key, value in context.items():
                message += f"• {key}: {value}\n"

        return message

    def _format_moderation_required_message(self, post: AdminPost, reason: str) -> str:
        """Форматирование сообщения о необходимости модерации"""
        return (
            f"⚠️ Требуется модерация\n\n"
            f"📝 Заголовок: {post.title}\n"
            f"🆔 ID поста: {post.id}\n"
            f"📋 Причина: {reason}\n"
            f"👤 Автор: {post.author_id}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

    def _format_quota_warning_message(
        self, quota_type: str, current_usage: int, limit: int
    ) -> str:
        """Форматирование сообщения о превышении квот"""
        percentage = (current_usage / limit) * 100
        return (
            f"⚠️ Предупреждение о квотах\n\n"
            f"📊 Тип квоты: {quota_type}\n"
            f"📈 Использовано: {current_usage} из {limit} ({percentage:.1f}%)\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

    # Приватные методы для работы с получателями и отправкой

    async def _get_notification_recipients(
        self, notification_type: NotificationType, admin_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Получение списка получателей уведомлений"""
        recipients = []

        if admin_id:
            # Конкретный админ
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and admin.is_admin:
                recipients.append(
                    {
                        "user_id": admin.id,
                        "telegram_id": admin.telegram_id,
                        "email": getattr(admin, "email", None),
                        "notification_settings": await self.get_notification_settings(
                            admin.id
                        ),
                    }
                )
        else:
            # Все админы
            recipients = await self._get_all_admin_recipients()

        return recipients

    async def _get_all_admin_recipients(self) -> list[dict[str, Any]]:
        """Получение всех админов как получателей"""
        try:
            stmt = select(User).where(User.is_admin)
            result = await self.session.execute(stmt)
            admins = result.scalars().all()

            recipients = []
            for admin in admins:
                recipients.append(
                    {
                        "user_id": admin.id,
                        "telegram_id": admin.telegram_id,
                        "email": getattr(admin, "email", None),
                        "notification_settings": await self.get_notification_settings(
                            admin.id
                        ),
                    }
                )

            return recipients

        except Exception as e:
            logger.error(f"Error getting admin recipients: {e}")
            return []

    async def _send_notifications(
        self,
        notification_type: NotificationType,
        message: str,
        recipients: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Отправка уведомлений через различные каналы"""
        settings = self.notification_settings.get(
            notification_type,
            {
                "priority": NotificationPriority.MEDIUM,
                "channels": self.default_channels,
            },
        )

        success_count = 0
        total_count = 0

        for recipient in recipients:
            for channel in settings["channels"]:
                total_count += 1

                try:
                    if channel == NotificationChannel.TELEGRAM:
                        success = await self._send_telegram_notification(
                            recipient["telegram_id"], message, metadata
                        )
                    elif channel == NotificationChannel.EMAIL:
                        success = await self._send_email_notification(
                            recipient["email"], message, metadata
                        )
                    elif channel == NotificationChannel.WEBHOOK:
                        success = await self._send_webhook_notification(
                            message, metadata
                        )
                    elif channel == NotificationChannel.IN_APP:
                        success = await self._send_in_app_notification(
                            recipient["user_id"], message, metadata
                        )
                    else:
                        success = False

                    if success:
                        success_count += 1

                except Exception as e:
                    logger.error(f"Error sending notification via {channel.value}: {e}")

        return success_count > 0

    async def _send_telegram_notification(
        self, telegram_id: int, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Отправка уведомления через Telegram"""
        try:
            # Здесь должна быть интеграция с Telegram Bot API
            # Пока логируем
            logger.info(f"Telegram notification to {telegram_id}: {message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False

    async def _send_email_notification(
        self, email: str | None, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Отправка уведомления по email"""
        try:
            if not email:
                return False

            # Здесь должна быть интеграция с email сервисом
            logger.info(f"Email notification to {email}: {message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False

    async def _send_webhook_notification(
        self, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Отправка уведомления через webhook"""
        try:
            # Здесь должна быть отправка webhook
            logger.info(f"Webhook notification: {message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False

    async def _send_in_app_notification(
        self, user_id: int, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Отправка внутреннего уведомления"""
        try:
            # Здесь должно быть сохранение в таблицу уведомлений
            logger.info(f"In-app notification to user {user_id}: {message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            return False

    # Утилитарные методы

    async def check_notification_health(self) -> dict[str, Any]:
        """Проверка работоспособности системы уведомлений"""
        health_status = {
            "status": "healthy",
            "channels": {},
            "last_check": datetime.now().isoformat(),
        }

        # Проверка каждого канала
        for channel in NotificationChannel:
            try:
                if channel == NotificationChannel.TELEGRAM:
                    # Проверка Telegram Bot API
                    health_status["channels"][channel.value] = "healthy"
                elif channel == NotificationChannel.EMAIL:
                    # Проверка email сервиса
                    health_status["channels"][channel.value] = "healthy"
                elif channel == NotificationChannel.WEBHOOK:
                    # Проверка webhook endpoint
                    health_status["channels"][channel.value] = "healthy"
                else:
                    health_status["channels"][channel.value] = "healthy"

            except Exception as e:
                health_status["channels"][channel.value] = f"error: {str(e)}"
                health_status["status"] = "degraded"

        return health_status

    async def get_notification_statistics(self, days: int = 7) -> dict[str, Any]:
        """Получение статистики уведомлений"""
        # В реальной реализации здесь был бы запрос к БД
        return {
            "period_days": days,
            "total_sent": 0,
            "by_type": {},
            "by_channel": {},
            "success_rate": 0.0,
            "generated_at": datetime.now().isoformat(),
        }
