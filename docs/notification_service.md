# NotificationService Documentation

## Обзор

`NotificationService` - это сервис для управления уведомлениями администраторов в Telegram-боте. Он обеспечивает централизованную систему отправки уведомлений о статусе публикаций, системных ошибках, необходимости модерации и других важных событиях.

## Возможности

### Типы уведомлений
- **POST_PUBLISHED** - Уведомления о успешной публикации постов
- **POST_FAILED** - Уведомления об ошибках публикации
- **POST_SCHEDULED** - Уведомления о запланированных публикациях
- **SYSTEM_ERROR** - Системные ошибки и предупреждения
- **MODERATION_REQUIRED** - Необходимость модерации контента
- **QUOTA_WARNING** - Предупреждения о превышении квот

### Приоритеты уведомлений
- **LOW** - Низкий приоритет (информационные сообщения)
- **MEDIUM** - Средний приоритет (важные уведомления)
- **HIGH** - Высокий приоритет (критические ошибки)
- **CRITICAL** - Критический приоритет (требует немедленного внимания)

### Каналы доставки
- **TELEGRAM** - Отправка через Telegram Bot API
- **EMAIL** - Отправка на электронную почту
- **WEBHOOK** - Отправка через веб-хуки
- **IN_APP** - Внутренние уведомления в приложении

## Архитектура

### Компоненты

```
NotificationService
├── Основные методы
│   ├── notify_post_published()     # Уведомления о публикации
│   ├── notify_post_failed()        # Уведомления об ошибках
│   ├── notify_post_scheduled()     # Уведомления о планировании
│   ├── notify_system_error()       # Системные ошибки
│   ├── notify_moderation_required() # Необходимость модерации
│   └── notify_quota_warning()      # Предупреждения о квотах
├── Массовые уведомления
│   └── send_bulk_notification()    # Отправка множественных уведомлений
├── Управление настройками
│   ├── get_notification_settings() # Получение настроек
│   └── update_notification_settings() # Обновление настроек
├── Мониторинг
│   ├── get_notification_history()  # История уведомлений
│   ├── get_notification_statistics() # Статистика
│   └── check_notification_health() # Проверка работоспособности
└── Внутренние методы
    ├── _format_message()           # Форматирование сообщений
    ├── _get_recipients()           # Получение получателей
    └── _send_notification()        # Отправка уведомлений
```

### Взаимодействие с другими сервисами

- **AdminPostService** - Получение уведомлений о статусе постов
- **UserService** - Управление настройками администраторов
- **Telegram Bot API** - Отправка уведомлений в Telegram
- **Email Service** - Отправка email-уведомлений
- **Webhook Service** - Отправка веб-хуков

## Установка

`NotificationService` автоматически интегрируется в проект через `UnitOfWork`:

```python
from database.unit_of_work import UnitOfWork

async with get_session() as session:
    uow = UnitOfWork(session)
    notification_service = uow.notification_service
```

## API Reference

### Уведомления о постах

#### notify_post_published
```python
async def notify_post_published(
    self,
    post_id: int,
    admin_id: Optional[int] = None,
    channels: Optional[List[NotificationChannel]] = None
) -> bool
```
Отправляет уведомление о успешной публикации поста.

**Параметры:**
- `post_id` - ID опубликованного поста
- `admin_id` - ID администратора (опционально)
- `channels` - Каналы доставки (опционально)

**Возвращает:** `bool` - Успешность отправки

#### notify_post_failed
```python
async def notify_post_failed(
    self,
    post_id: int,
    error_message: str,
    admin_id: Optional[int] = None,
    channels: Optional[List[NotificationChannel]] = None
) -> bool
```
Отправляет уведомление об ошибке публикации.

**Параметры:**
- `post_id` - ID поста с ошибкой
- `error_message` - Описание ошибки
- `admin_id` - ID администратора (опционально)
- `channels` - Каналы доставки (опционально)

#### notify_post_scheduled
```python
async def notify_post_scheduled(
    self,
    post_id: int,
    scheduled_time: datetime,
    admin_id: Optional[int] = None,
    channels: Optional[List[NotificationChannel]] = None
) -> bool
```
Отправляет уведомление о запланированной публикации.

### Системные уведомления

#### notify_system_error
```python
async def notify_system_error(
    self,
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
    priority: NotificationPriority = NotificationPriority.HIGH
) -> bool
```
Отправляет уведомление о системной ошибке.

#### notify_moderation_required
```python
async def notify_moderation_required(
    self,
    post_id: int,
    reason: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> bool
```
Отправляет уведомление о необходимости модерации.

#### notify_quota_warning
```python
async def notify_quota_warning(
    self,
    quota_type: str,
    current_usage: int,
    limit: int,
    admin_id: Optional[int] = None
) -> bool
```
Отправляет предупреждение о превышении квот.

### Массовые уведомления

#### send_bulk_notification
```python
async def send_bulk_notification(
    self,
    notification_type: NotificationType,
    message: str,
    admin_ids: List[int],
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    channels: Optional[List[NotificationChannel]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[int, bool]
```
Отправляет уведомление множественным получателям.

### Управление настройками

#### get_notification_settings
```python
async def get_notification_settings(
    self,
    admin_id: int
) -> Dict[str, Any]
```
Получает настройки уведомлений администратора.

#### update_notification_settings
```python
async def update_notification_settings(
    self,
    admin_id: int,
    settings: Dict[str, Any]
) -> bool
```
Обновляет настройки уведомлений.

### Мониторинг и статистика

#### get_notification_history
```python
async def get_notification_history(
    self,
    admin_id: Optional[int] = None,
    notification_type: Optional[NotificationType] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]
```
Получает историю уведомлений.

#### get_notification_statistics
```python
async def get_notification_statistics(
    self,
    days: int = 30
) -> Dict[str, Any]
```
Получает статистику уведомлений.

#### check_notification_health
```python
async def check_notification_health(self) -> Dict[str, Any]
```
Проверяет работоспособность системы уведомлений.

## Примеры использования

### Базовое использование

```python
from database.unit_of_work import UnitOfWork
from database.services.notification_service import NotificationType

async with get_session() as session:
    uow = UnitOfWork(session)
    notification_service = uow.notification_service
    
    # Уведомление о публикации
    await notification_service.notify_post_published(
        post_id=1,
        admin_id=1
    )
    
    # Уведомление об ошибке
    await notification_service.notify_system_error(
        error_type="DatabaseError",
        error_message="Не удалось подключиться к базе данных"
    )
```

### Массовые уведомления

```python
# Отправка уведомления всем админам
admin_ids = [1, 2, 3]
results = await notification_service.send_bulk_notification(
    notification_type=NotificationType.SYSTEM_ERROR,
    message="Запланированное техническое обслуживание",
    admin_ids=admin_ids
)
```

### Настройка уведомлений

```python
# Обновление настроек
settings = {
    "post_published": {
        "enabled": True,
        "channels": ["telegram", "email"]
    },
    "quiet_hours": {
        "enabled": True,
        "start": "22:00",
        "end": "08:00"
    }
}

await notification_service.update_notification_settings(
    admin_id=1,
    settings=settings
)
```

## Интеграция с Telegram Bot

### Обработчик уведомлений

```python
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class TelegramNotificationHandler:
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_admin_notification(self, admin_telegram_id: int, message: str):
        """Отправка уведомления админу"""
        try:
            await self.bot.send_message(
                chat_id=admin_telegram_id,
                text=message,
                parse_mode="HTML"
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            return False
    
    async def send_notification_with_actions(self, admin_telegram_id: int, 
                                           message: str, post_id: int):
        """Отправка уведомления с кнопками действий"""
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
            ]
        ])
        
        await self.bot.send_message(
            chat_id=admin_telegram_id,
            text=message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
```

### Обработка callback'ов

```python
from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(lambda c: c.data.startswith('edit_post_'))
async def handle_edit_post(callback: CallbackQuery):
    post_id = int(callback.data.split('_')[-1])
    
    # Логика редактирования поста
    await callback.message.edit_text(
        f"Редактирование поста {post_id}..."
    )

@router.callback_query(lambda c: c.data.startswith('delete_post_'))
async def handle_delete_post(callback: CallbackQuery):
    post_id = int(callback.data.split('_')[-1])
    
    # Логика удаления поста
    await callback.message.edit_text(
        f"Пост {post_id} удален"
    )
```

## Структуры данных

### NotificationType
```python
class NotificationType(str, Enum):
    POST_PUBLISHED = "post_published"
    POST_FAILED = "post_failed"
    POST_SCHEDULED = "post_scheduled"
    SYSTEM_ERROR = "system_error"
    MODERATION_REQUIRED = "moderation_required"
    QUOTA_WARNING = "quota_warning"
```

### NotificationPriority
```python
class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### NotificationChannel
```python
class NotificationChannel(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
```

## Конфигурация

### Настройки по умолчанию

```python
DEFAULT_NOTIFICATION_SETTINGS = {
    "post_published": {
        "enabled": True,
        "channels": ["telegram"]
    },
    "post_failed": {
        "enabled": True,
        "channels": ["telegram", "email"]
    },
    "system_error": {
        "enabled": True,
        "channels": ["telegram", "email"]
    },
    "quiet_hours": {
        "enabled": False,
        "start": "22:00",
        "end": "08:00"
    }
}
```

### Переменные окружения

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Webhook
WEBHOOK_URL=https://your-webhook-url.com/notifications
WEBHOOK_SECRET=your_webhook_secret
```

## Производительность

### Оптимизации

1. **Асинхронная отправка** - Все уведомления отправляются асинхронно
2. **Батчинг** - Группировка уведомлений для массовой отправки
3. **Кэширование настроек** - Кэширование настроек администраторов
4. **Retry механизм** - Повторные попытки при ошибках
5. **Rate limiting** - Ограничение частоты отправки

### Метрики производительности

```python
# Получение статистики производительности
stats = await notification_service.get_notification_statistics(days=7)
print(f"Среднее время отправки: {stats['avg_send_time']}ms")
print(f"Успешность доставки: {stats['success_rate']}%")
print(f"Ошибки по каналам: {stats['errors_by_channel']}")
```

## Безопасность

### Меры безопасности

1. **Валидация данных** - Проверка всех входящих параметров
2. **Санитизация сообщений** - Очистка от потенциально опасного контента
3. **Ограничение доступа** - Проверка прав администратора
4. **Логирование** - Запись всех операций с уведомлениями
5. **Шифрование** - Шифрование чувствительных данных

### Аудит безопасности

```python
# Проверка безопасности
security_check = await notification_service.check_security_status()
if not security_check['is_secure']:
    logger.warning(f"Проблемы безопасности: {security_check['issues']}")
```

## Мониторинг и логирование

### Логирование

```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('notification_service')
```

### Метрики

```python
# Мониторинг ключевых метрик
metrics = {
    'notifications_sent_total': 0,
    'notifications_failed_total': 0,
    'avg_delivery_time': 0,
    'active_channels': [],
    'error_rate_by_type': {}
}
```

## Расширения

### Добавление новых каналов

```python
class CustomNotificationChannel:
    async def send_notification(self, recipient: str, message: str) -> bool:
        # Реализация отправки через кастомный канал
        pass

# Регистрация канала
notification_service.register_channel('custom', CustomNotificationChannel())
```

### Кастомные типы уведомлений

```python
# Добавление нового типа уведомления
class CustomNotificationType(str, Enum):
    USER_MILESTONE = "user_milestone"
    CONTENT_TRENDING = "content_trending"
    SECURITY_ALERT = "security_alert"
```

### Шаблоны сообщений

```python
# Кастомные шаблоны
CUSTOM_TEMPLATES = {
    'achievement': {
        'title': '🎉 Достижение разблокировано!',
        'body': 'Поздравляем! Вы достигли {milestone} {metric}!'
    },
    'security_alert': {
        'title': '🔒 Предупреждение безопасности',
        'body': 'Обнаружена подозрительная активность: {details}'
    }
}
```

## Troubleshooting

### Частые проблемы

1. **Уведомления не доставляются**
   - Проверьте настройки каналов
   - Убедитесь в корректности токенов
   - Проверьте логи на ошибки

2. **Медленная отправка**
   - Проверьте нагрузку на сервер
   - Оптимизируйте размер сообщений
   - Используйте батчинг

3. **Ошибки авторизации**
   - Проверьте токены API
   - Убедитесь в правильности настроек

### Диагностика

```python
# Диагностика системы
diagnostics = await notification_service.run_diagnostics()
for check, result in diagnostics.items():
    print(f"{check}: {'✅' if result['status'] == 'ok' else '❌'} {result['message']}")
```

## Заключение

`NotificationService` предоставляет мощную и гибкую систему уведомлений для Telegram-бота. Сервис поддерживает множественные каналы доставки, настраиваемые приоритеты, массовые уведомления и подробную аналитику.

Для получения дополнительной информации обратитесь к примерам использования в `examples/notification_service_usage.py`.