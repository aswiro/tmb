# SchedulerService - Сервис планирования постов

## Описание

`SchedulerService` предоставляет функциональность для планирования и автоматической публикации постов в Telegram каналы и группы. Сервис интегрирован с APScheduler для надежного выполнения задач по расписанию.

## Архитектура

### Компоненты

1. **SchedulerService** (`database/services/scheduler_service.py`) - основной сервис для работы с запланированными постами в базе данных
2. **PostScheduler** (`utilities/post_scheduler.py`) - обертка над APScheduler для управления заданиями
3. **AdminPostService** - сервис для управления постами (создание, редактирование, публикация)

### Схема работы

```
[Пользователь] -> [AdminPostService] -> [SchedulerService] -> [PostScheduler] -> [APScheduler] -> [Redis]
                                    ↓
                              [База данных]
```

## Установка зависимостей

```bash
pip install -r requirements_scheduler.txt
```

## Настройка

### Redis

Планировщик использует Redis для хранения заданий:

```python
# Настройки Redis в PostScheduler
redis_url = "redis://localhost:6379/1"
```

### Инициализация

```python
from utilities.post_scheduler import init_post_scheduler

# Инициализация планировщика
scheduler = await init_post_scheduler(redis_url="redis://localhost:6379/1")
```

## Использование

### Создание и планирование поста

```python
from database import get_session
from database.unit_of_work import UnitOfWork
from utilities.post_scheduler import get_post_scheduler
from datetime import datetime, timedelta

async def schedule_post_example():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # 1. Создаем черновик
        draft = await uow.admin_post_service.create_draft(
            user_id=1,
            content="Привет! Это запланированный пост",
            media_urls=["https://example.com/image.jpg"]
        )
        
        # 2. Планируем публикацию
        scheduled_time = datetime.now() + timedelta(hours=2)
        scheduled_post = await uow.admin_post_service.schedule_post(
            draft.id,
            scheduled_time,
            target_groups=["@my_channel", "@my_group"]
        )
        
        # 3. Добавляем в планировщик
        scheduler = await get_post_scheduler()
        await scheduler.schedule_post(scheduled_post.id, scheduled_time)
        
        await uow.commit()
```

### Создание поста с опросом

```python
async def create_poll_example():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        poll_post = await uow.admin_post_service.create_poll_post(
            user_id=1,
            question="Какой фреймворк лучше?",
            options=["FastAPI", "Django", "Flask"],
            allows_multiple_answers=False,
            is_anonymous=True
        )
        
        await uow.commit()
```

### Управление запланированными постами

```python
# Перепланирование
new_time = datetime.now() + timedelta(hours=3)
await uow.scheduler_service.reschedule_post(post_id, new_time)

# Отмена
await uow.admin_post_service.cancel_post(post_id, "Отменено пользователем")

# Получение статистики
stats = await uow.scheduler_service.get_scheduler_stats()
print(f"Запланировано: {stats['scheduled_count']}")
print(f"Опубликовано: {stats['published_count']}")
```

## API SchedulerService

### Основные методы

#### `check_scheduled_posts()`
Проверяет и публикует посты, готовые к публикации.

#### `publish_scheduled_post(post: AdminPost) -> bool`
Публикует конкретный запланированный пост.

#### `expire_posts()`
Обрабатывает истекшие посты (старше 24 часов).

#### `get_next_scheduled_posts(limit: int = 10) -> List[AdminPost]`
Возвращает следующие запланированные посты.

#### `reschedule_post(post_id: int, new_scheduled_at: datetime) -> AdminPost | None`
Перепланирует пост на новое время.

#### `get_scheduler_stats() -> dict`
Возвращает статистику планировщика.

## API PostScheduler

### Основные методы

#### `start()`
Запускает планировщик и периодические задачи.

#### `stop()`
Останавливает планировщик.

#### `schedule_post(post_id: int, scheduled_at: datetime) -> bool`
Добавляет задание на публикацию поста.

#### `cancel_scheduled_post(post_id: int) -> bool`
Отменяет запланированную публикацию.

#### `reschedule_post(post_id: int, new_scheduled_at: datetime) -> bool`
Перепланирует публикацию поста.

#### `get_scheduled_jobs() -> list`
Возвращает список активных заданий.

#### `get_scheduler_status() -> dict`
Возвращает статус планировщика.

## Периодические задачи

Планировщик автоматически выполняет следующие задачи:

1. **Проверка запланированных постов** - каждую минуту
2. **Очистка истекших постов** - каждый час

## Обработка ошибок

При ошибке публикации пост автоматически помечается статусом `ERROR`:

```python
# Получение постов с ошибками
error_posts = await uow.admin_post_service.get_posts_with_errors()

for post in error_posts:
    print(f"Пост {post.id}: {post.error_message}")
```

## Мониторинг

### Логирование

Все операции логируются с помощью `loguru`:

```python
from loguru import logger

# Логи планировщика
logger.info("Post scheduler started")
logger.error(f"Error publishing post {post_id}: {error}")
```

### Статистика

```python
# Статистика из базы данных
db_stats = await uow.scheduler_service.get_scheduler_stats()

# Статистика планировщика
scheduler_stats = await scheduler.get_scheduler_status()

print(f"Запланировано в БД: {db_stats['scheduled_count']}")
print(f"Активных заданий: {scheduler_stats['scheduled_jobs']}")
```

## Интеграция с Telegram Bot

```python
# В обработчике команды бота
@router.message(Command("schedule"))
async def schedule_post_handler(message: Message, session: AsyncSession):
    uow = UnitOfWork(session)
    
    # Создаем и планируем пост
    draft = await uow.admin_post_service.create_draft(
        user_id=message.from_user.id,
        content=message.text
    )
    
    scheduled_time = datetime.now() + timedelta(hours=1)
    scheduled_post = await uow.admin_post_service.schedule_post(
        draft.id,
        scheduled_time,
        target_groups=["@my_channel"]
    )
    
    # Добавляем в планировщик
    scheduler = await get_post_scheduler()
    await scheduler.schedule_post(scheduled_post.id, scheduled_time)
    
    await uow.commit()
    
    await message.reply(f"Пост запланирован на {scheduled_time}")
```

## Примеры использования

Полные примеры использования доступны в файле `examples/scheduler_usage.py`.

## Безопасность

1. **Валидация времени** - проверка корректности времени планирования
2. **Ограничения** - максимальное количество одновременных заданий
3. **Очистка** - автоматическое удаление истекших постов
4. **Логирование** - подробное логирование всех операций

## Производительность

- **Redis** для быстрого доступа к заданиям
- **Асинхронность** для неблокирующих операций
- **Пакетная обработка** для оптимизации запросов к БД
- **Ограничение ресурсов** через настройки APScheduler

## Расширение функциональности

### Добавление новых типов постов

```python
# В SchedulerService
async def publish_video_post(self, post: AdminPost) -> bool:
    # Логика публикации видео поста
    pass
```

### Интеграция с внешними сервисами

```python
# Отправка уведомлений
async def send_notification(self, post_id: int, status: str):
    # Отправка уведомления через webhook
    pass
```

### Аналитика

```python
# Сбор метрик публикации
async def track_publication_metrics(self, post: AdminPost):
    # Сохранение метрик в аналитику
    pass
```