"""Примеры использования NotificationService"""

import asyncio
from datetime import datetime, timedelta
from database import get_session
from database.unit_of_work import UnitOfWork
from database.services.notification_service import NotificationType, NotificationPriority


async def example_post_notifications():
    """Примеры уведомлений о постах"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        notification_service = uow.notification_service
        
        print("=== Уведомления о постах ===")
        
        # Уведомление о успешной публикации
        success = await notification_service.notify_post_published(
            post_id=1,
            admin_id=1
        )
        print(f"Уведомление о публикации отправлено: {success}")
        
        # Уведомление об ошибке публикации
        success = await notification_service.notify_post_failed(
            post_id=2,
            error_message="Превышен лимит символов в сообщении",
            admin_id=1
        )
        print(f"Уведомление об ошибке отправлено: {success}")
        
        # Уведомление о запланированной публикации
        scheduled_time = datetime.now() + timedelta(hours=2)
        success = await notification_service.notify_post_scheduled(
            post_id=3,
            scheduled_time=scheduled_time,
            admin_id=1
        )
        print(f"Уведомление о планировании отправлено: {success}")


async def example_system_notifications():
    """Примеры системных уведомлений"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        notification_service = uow.notification_service
        
        print("\n=== Системные уведомления ===")
        
        # Уведомление о системной ошибке
        success = await notification_service.notify_system_error(
            error_type="DatabaseConnectionError",
            error_message="Не удалось подключиться к базе данных",
            context={
                "host": "localhost",
                "port": 5432,
                "database": "tmb_bot",
                "retry_count": 3
            }
        )
        print(f"Уведомление о системной ошибке отправлено: {success}")
        
        # Уведомление о необходимости модерации
        success = await notification_service.notify_moderation_required(
            post_id=4,
            reason="Обнаружены потенциально спорные материалы"
        )
        print(f"Уведомление о модерации отправлено: {success}")
        
        # Уведомление о превышении квот
        success = await notification_service.notify_quota_warning(
            quota_type="daily_posts",
            current_usage=95,
            limit=100,
            admin_id=1
        )
        print(f"Уведомление о квотах отправлено: {success}")


async def example_bulk_notifications():
    """Пример массовой отправки уведомлений"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        notification_service = uow.notification_service
        
        print("\n=== Массовые уведомления ===")
        
        # Отправка уведомления всем админам
        admin_ids = [1, 2, 3]  # ID админов
        results = await notification_service.send_bulk_notification(
            notification_type=NotificationType.SYSTEM_ERROR,
            message="🔧 Запланированное техническое обслуживание\n\nСистема будет недоступна с 02:00 до 04:00 МСК",
            admin_ids=admin_ids,
            metadata={
                "maintenance_start": "2024-01-15T02:00:00",
                "maintenance_end": "2024-01-15T04:00:00",
                "affected_services": ["posting", "analytics"]
            }
        )
        
        print("Результаты массовой отправки:")
        for admin_id, success in results.items():
            print(f"  Админ {admin_id}: {'✅' if success else '❌'}")


async def example_notification_settings():
    """Примеры работы с настройками уведомлений"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        notification_service = uow.notification_service
        
        print("\n=== Настройки уведомлений ===")
        
        # Получение текущих настроек
        settings = await notification_service.get_notification_settings(admin_id=1)
        print(f"Текущие настройки: {len(settings)} типов уведомлений")
        
        # Обновление настроек
        new_settings = {
            "post_published": {
                "enabled": True,
                "channels": ["telegram", "email"]
            },
            "system_error": {
                "enabled": True,
                "channels": ["telegram", "email", "webhook"]
            },
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00"
            }
        }
        
        success = await notification_service.update_notification_settings(
            admin_id=1,
            settings=new_settings
        )
        print(f"Настройки обновлены: {success}")


async def example_notification_monitoring():
    """Примеры мониторинга системы уведомлений"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        notification_service = uow.notification_service
        
        print("\n=== Мониторинг уведомлений ===")
        
        # Проверка работоспособности
        health = await notification_service.check_notification_health()
        print(f"Статус системы: {health['status']}")
        print("Статус каналов:")
        for channel, status in health['channels'].items():
            print(f"  {channel}: {status}")
        
        # Получение статистики
        stats = await notification_service.get_notification_statistics(days=7)
        print(f"\nСтатистика за {stats['period_days']} дней:")
        print(f"  Всего отправлено: {stats['total_sent']}")
        print(f"  Успешность: {stats['success_rate']:.1f}%")
        
        # История уведомлений
        history = await notification_service.get_notification_history(
            admin_id=1,
            limit=10
        )
        print(f"\nПоследние {len(history)} уведомлений для админа 1")


async def example_telegram_bot_integration():
    """Пример интеграции с Telegram ботом"""
    print("\n=== Интеграция с Telegram Bot ===")
    
    # Пример обработчика для отправки уведомлений через бота
    class TelegramNotificationHandler:
        def __init__(self, bot):
            self.bot = bot
        
        async def send_admin_notification(self, admin_telegram_id: int, message: str):
            """Отправка уведомления админу через бота"""
            try:
                await self.bot.send_message(
                    chat_id=admin_telegram_id,
                    text=message,
                    parse_mode="HTML"
                )
                return True
            except Exception as e:
                print(f"Ошибка отправки уведомления: {e}")
                return False
        
        async def send_notification_with_buttons(self, admin_telegram_id: int, 
                                               message: str, post_id: int):
            """Отправка уведомления с кнопками действий"""
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Редактировать",
                        callback_data=f"edit_post_{post_id}"
                    ),
                    InlineKeyboardButton(
                        text="🗑 Удалить",
                        callback_data=f"delete_post_{post_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Статистика",
                        callback_data=f"stats_post_{post_id}"
                    )
                ]
            ])
            
            try:
                await self.bot.send_message(
                    chat_id=admin_telegram_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return True
            except Exception as e:
                print(f"Ошибка отправки уведомления с кнопками: {e}")
                return False
    
    print("Пример интеграции создан. Используйте TelegramNotificationHandler в вашем боте.")


async def example_custom_notification_types():
    """Примеры создания кастомных типов уведомлений"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        notification_service = uow.notification_service
        
        print("\n=== Кастомные уведомления ===")
        
        # Уведомление о достижении
        await notification_service.send_bulk_notification(
            notification_type=NotificationType.SYSTEM_ERROR,  # Используем существующий тип
            message=(
                "🎉 Поздравляем!\n\n"
                "Ваш бот достиг 1000 подписчиков!\n"
                "📈 Рост за месяц: +250 пользователей\n"
                "🔥 Самый популярный пост: 'Новости технологий'"
            ),
            admin_ids=[1],
            metadata={
                "achievement_type": "subscriber_milestone",
                "milestone_value": 1000,
                "growth_period": "month",
                "growth_value": 250
            }
        )
        
        # Уведомление о безопасности
        await notification_service.notify_system_error(
            error_type="SecurityAlert",
            error_message="Обнаружена подозрительная активность",
            context={
                "event_type": "multiple_failed_logins",
                "ip_address": "192.168.1.100",
                "attempts": 5,
                "time_window": "5 minutes",
                "action_taken": "temporary_ip_block"
            }
        )
        
        print("Кастомные уведомления отправлены")


async def main():
    """Главная функция с примерами"""
    print("🔔 Примеры использования NotificationService\n")
    
    try:
        await example_post_notifications()
        await example_system_notifications()
        await example_bulk_notifications()
        await example_notification_settings()
        await example_notification_monitoring()
        await example_telegram_bot_integration()
        await example_custom_notification_types()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")


if __name__ == "__main__":
    asyncio.run(main())