# PostAnalyticsService Documentation

## Обзор

`PostAnalyticsService` - это сервис для отслеживания и анализа взаимодействий пользователей с постами в Telegram-боте. Он предоставляет комплексную систему аналитики, включающую отслеживание просмотров, кликов, репостов, реакций и времени просмотра.

## Архитектура

### Компоненты

1. **PostAnalyticsService** - основной сервис для работы с аналитикой
2. **PostAnalytics** - модель данных для хранения метрик
3. **AdminPost** - модель постов, с которыми связана аналитика
4. **UnitOfWork** - паттерн для управления транзакциями

### Взаимодействие с другими компонентами

- **AdminPostService** - для работы с постами
- **SchedulerService** - для автоматизированной аналитики
- **Telegram Bot** - для отслеживания взаимодействий в реальном времени

## Установка и настройка

### Зависимости

Сервис использует стандартные зависимости проекта:
- SQLAlchemy (async)
- PostgreSQL
- Python 3.12+

### Инициализация

```python
from database import get_session
from database.unit_of_work import UnitOfWork

async with get_session() as session:
    uow = UnitOfWork(session)
    analytics_service = uow.post_analytics_service
```

## Основные возможности

### 1. Отслеживание взаимодействий

#### Просмотры
```python
# Отслеживание просмотра поста
await analytics_service.track_view(post_id=123, group_id=-1001234567890)
```

#### Клики
```python
# Отслеживание клика по посту
await analytics_service.track_click(post_id=123, group_id=-1001234567890)
```

#### Репосты/Пересылки
```python
# Отслеживание репоста
await analytics_service.track_share(post_id=123, group_id=-1001234567890)
```

#### Реакции
```python
# Отслеживание реакций
await analytics_service.track_reaction(post_id=123, group_id=-1001234567890, reaction="👍")
await analytics_service.track_reaction(post_id=123, group_id=-1001234567890, reaction="❤️")
```

#### Время просмотра
```python
# Отслеживание времени просмотра (в секундах)
await analytics_service.track_view_duration(post_id=123, group_id=-1001234567890, duration_seconds=45)
```

### 2. Получение аналитики

#### Аналитика по посту
```python
analytics = await analytics_service.get_post_analytics(post_id=123)

print(f"Просмотры: {analytics['total_views']}")
print(f"Клики: {analytics['total_clicks']}")
print(f"CTR: {analytics['average_ctr']}%")
print(f"Вовлеченность: {analytics['average_engagement']}%")
```

#### Сводная аналитика за период
```python
from datetime import datetime, timedelta

date_from = datetime.now() - timedelta(days=7)
date_to = datetime.now()

summary = await analytics_service.get_analytics_summary(date_from, date_to)

print(f"Постов за период: {summary['posts_count']}")
print(f"Общие просмотры: {summary['total_views']}")
print(f"Топ постов: {summary['top_posts']}")
```

#### Аналитика по группе
```python
group_analytics = await analytics_service.get_group_analytics(
    group_id=-1001234567890, 
    days=30
)

print(f"Постов в группе: {group_analytics['posts_count']}")
print(f"Средний CTR: {group_analytics['average_ctr']}%")
```

#### Популярные реакции
```python
reactions = await analytics_service.get_popular_reactions(days=30)

for reaction, count in reactions.items():
    print(f"{reaction}: {count}")
```

## API Reference

### PostAnalyticsService

#### Методы отслеживания

| Метод | Описание | Параметры | Возвращает |
|-------|----------|-----------|------------|
| `track_view()` | Отслеживание просмотра | `post_id`, `group_id` | `bool` |
| `track_click()` | Отслеживание клика | `post_id`, `group_id` | `bool` |
| `track_share()` | Отслеживание репоста | `post_id`, `group_id` | `bool` |
| `track_reaction()` | Отслеживание реакции | `post_id`, `group_id`, `reaction` | `bool` |
| `track_view_duration()` | Отслеживание времени просмотра | `post_id`, `group_id`, `duration_seconds` | `bool` |

#### Методы получения данных

| Метод | Описание | Параметры | Возвращает |
|-------|----------|-----------|------------|
| `get_post_analytics()` | Аналитика поста | `post_id` | `dict` |
| `get_analytics_summary()` | Сводная аналитика | `date_from`, `date_to` | `dict` |
| `get_group_analytics()` | Аналитика группы | `group_id`, `days=30` | `dict` |
| `get_popular_reactions()` | Популярные реакции | `days=30` | `dict` |

#### Служебные методы

| Метод | Описание | Параметры | Возвращает |
|-------|----------|-----------|------------|
| `delete_post_analytics()` | Удаление аналитики поста | `post_id` | `bool` |

## Структура данных

### Аналитика поста
```python
{
    "total_views": 1500,
    "total_clicks": 150,
    "total_shares": 25,
    "total_reactions": {"👍": 45, "❤️": 30, "😂": 15},
    "average_ctr": 10.0,
    "average_engagement": 14.0,
    "groups_count": 3,
    "by_groups": [
        {
            "group_id": -1001234567890,
            "views": 500,
            "clicks": 50,
            "shares": 8,
            "reactions": {"👍": 15, "❤️": 10},
            "ctr": 10.0,
            "engagement": 13.6,
            "view_duration": 42
        }
    ]
}
```

### Сводная аналитика
```python
{
    "period": {
        "from": "2024-01-01T00:00:00",
        "to": "2024-01-07T23:59:59"
    },
    "posts_count": 25,
    "total_views": 15000,
    "total_clicks": 1200,
    "total_shares": 180,
    "total_reactions": {"👍": 450, "❤️": 300},
    "average_ctr": 8.0,
    "average_engagement": 12.8,
    "top_posts": [
        {
            "post_id": 123,
            "title": "Заголовок поста",
            "views": 2000,
            "clicks": 200,
            "shares": 30,
            "reactions": 85,
            "ctr": 10.0
        }
    ]
}
```

## Интеграция с Telegram Bot

### Отслеживание взаимодействий

```python
from aiogram import types
from database import get_session
from database.unit_of_work import UnitOfWork

# Отслеживание просмотра при отправке поста
@dp.message_handler(content_types=['text'])
async def track_post_view(message: types.Message):
    if message.reply_to_message and message.reply_to_message.from_user.is_bot:
        # Это просмотр поста от бота
        post_id = extract_post_id(message.reply_to_message)
        group_id = message.chat.id
        
        async with get_session() as session:
            uow = UnitOfWork(session)
            await uow.post_analytics_service.track_view(post_id, group_id)
            await uow.commit()

# Отслеживание кликов по inline кнопкам
@dp.callback_query_handler(lambda c: c.data.startswith('post_'))
async def track_post_click(callback_query: types.CallbackQuery):
    post_id = int(callback_query.data.split('_')[1])
    group_id = callback_query.message.chat.id
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        await uow.post_analytics_service.track_click(post_id, group_id)
        await uow.commit()
    
    await callback_query.answer("Переход зафиксирован!")

# Команда для получения статистики
@dp.message_handler(commands=['stats'])
async def get_post_stats(message: types.Message):
    try:
        post_id = int(message.get_args())
    except (ValueError, TypeError):
        await message.reply("Укажите ID поста: /stats 123")
        return
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        analytics = await uow.post_analytics_service.get_post_analytics(post_id)
        
        if not analytics or analytics['total_views'] == 0:
            await message.reply(f"Статистика для поста {post_id} не найдена")
            return
        
        text = f"📊 Статистика поста {post_id}:\n\n"
        text += f"👀 Просмотры: {analytics['total_views']}\n"
        text += f"👆 Клики: {analytics['total_clicks']}\n"
        text += f"📤 Репосты: {analytics['total_shares']}\n"
        text += f"📈 CTR: {analytics['average_ctr']}%\n"
        text += f"💫 Вовлеченность: {analytics['average_engagement']}%"
        
        await message.reply(text)
```

### Автоматическое отслеживание реакций

```python
# Webhook для отслеживания реакций (если доступно)
@dp.message_reaction_handler()
async def track_reaction(message_reaction: types.MessageReactionUpdated):
    post_id = extract_post_id(message_reaction.message)
    group_id = message_reaction.chat.id
    
    for reaction in message_reaction.new_reaction:
        if reaction.type == "emoji":
            async with get_session() as session:
                uow = UnitOfWork(session)
                await uow.post_analytics_service.track_reaction(
                    post_id, group_id, reaction.emoji
                )
                await uow.commit()
```

## Мониторинг и отчеты

### Ежедневные отчеты

```python
import asyncio
from datetime import datetime, timedelta

async def daily_analytics_report():
    """Ежедневный отчет по аналитике"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()
        
        summary = await uow.post_analytics_service.get_analytics_summary(
            yesterday, today
        )
        
        # Отправка отчета администраторам
        report = f"📊 Ежедневный отчет\n\n"
        report += f"📅 Дата: {yesterday.strftime('%d.%m.%Y')}\n"
        report += f"📝 Постов: {summary['posts_count']}\n"
        report += f"👀 Просмотров: {summary['total_views']}\n"
        report += f"👆 Кликов: {summary['total_clicks']}\n"
        report += f"📈 Средний CTR: {summary['average_ctr']}%\n"
        
        # Отправка через бота администраторам
        # await bot.send_message(ADMIN_CHAT_ID, report)

# Запуск через планировщик
# scheduler.add_job(daily_analytics_report, 'cron', hour=9, minute=0)
```

### Еженедельные отчеты

```python
async def weekly_analytics_report():
    """Еженедельный отчет с топ-постами"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        week_ago = datetime.now() - timedelta(days=7)
        now = datetime.now()
        
        summary = await uow.post_analytics_service.get_analytics_summary(
            week_ago, now
        )
        
        report = f"📊 Еженедельный отчет\n\n"
        report += f"📅 Период: {week_ago.strftime('%d.%m')} - {now.strftime('%d.%m.%Y')}\n"
        report += f"📝 Постов: {summary['posts_count']}\n"
        report += f"👀 Просмотров: {summary['total_views']}\n"
        report += f"📈 Средний CTR: {summary['average_ctr']}%\n\n"
        
        report += "🏆 Топ-5 постов:\n"
        for i, post in enumerate(summary['top_posts'][:5], 1):
            report += f"{i}. {post['title'][:30]}...\n"
            report += f"   👀 {post['views']} | 📈 {post['ctr']}%\n"
        
        # Отправка отчета
        # await bot.send_message(ADMIN_CHAT_ID, report)
```

## Производительность

### Оптимизация запросов

1. **Индексы**: Убедитесь, что созданы индексы для:
   - `post_id` и `group_id` в таблице `post_analytics`
   - `created_at` для временных запросов
   - `published_at` в таблице `admin_posts`

2. **Пакетная обработка**: Для высоконагруженных систем рассмотрите пакетную обработку метрик:

```python
# Пример пакетного обновления
async def batch_track_views(view_data: list[dict]):
    """Пакетное отслеживание просмотров"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        for data in view_data:
            await uow.post_analytics_service.track_view(
                data['post_id'], data['group_id']
            )
        
        await uow.commit()
```

3. **Кэширование**: Используйте Redis для кэширования часто запрашиваемой аналитики:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def get_cached_post_analytics(post_id: int):
    """Получение аналитики с кэшированием"""
    cache_key = f"post_analytics:{post_id}"
    
    # Проверяем кэш
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Получаем из БД
    async with get_session() as session:
        uow = UnitOfWork(session)
        analytics = await uow.post_analytics_service.get_post_analytics(post_id)
    
    # Кэшируем на 5 минут
    redis_client.setex(cache_key, 300, json.dumps(analytics))
    
    return analytics
```

## Безопасность

### Валидация данных

```python
def validate_post_id(post_id: int) -> bool:
    """Валидация ID поста"""
    return isinstance(post_id, int) and post_id > 0

def validate_group_id(group_id: int) -> bool:
    """Валидация ID группы"""
    return isinstance(group_id, int) and group_id != 0

def validate_reaction(reaction: str) -> bool:
    """Валидация реакции"""
    allowed_reactions = ["👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩"]
    return reaction in allowed_reactions
```

### Ограничение доступа

```python
# Проверка прав доступа к аналитике
async def check_analytics_access(user_id: int, post_id: int) -> bool:
    """Проверка прав доступа к аналитике поста"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Проверяем, является ли пользователь автором поста или админом
        post = await uow.admin_posts.get_by_id(post_id)
        if not post:
            return False
        
        user = await uow.users.get_by_id(user_id)
        if not user:
            return False
        
        return post.author_id == user_id or user.is_admin
```

## Расширения и интеграции

### Экспорт данных

```python
import csv
import io

async def export_analytics_csv(date_from: datetime, date_to: datetime) -> str:
    """Экспорт аналитики в CSV"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        summary = await uow.post_analytics_service.get_analytics_summary(
            date_from, date_to
        )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow(['Post ID', 'Title', 'Views', 'Clicks', 'Shares', 'CTR'])
    
    # Данные
    for post in summary['top_posts']:
        writer.writerow([
            post['post_id'],
            post['title'],
            post['views'],
            post['clicks'],
            post['shares'],
            post['ctr']
        ])
    
    return output.getvalue()
```

### Webhook интеграции

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/webhook/analytics")
async def analytics_webhook(data: dict, background_tasks: BackgroundTasks):
    """Webhook для внешних систем аналитики"""
    background_tasks.add_task(process_external_analytics, data)
    return {"status": "accepted"}

async def process_external_analytics(data: dict):
    """Обработка внешних данных аналитики"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        if data['event'] == 'view':
            await uow.post_analytics_service.track_view(
                data['post_id'], data['group_id']
            )
        elif data['event'] == 'click':
            await uow.post_analytics_service.track_click(
                data['post_id'], data['group_id']
            )
        
        await uow.commit()
```

## Заключение

`PostAnalyticsService` предоставляет мощную и гибкую систему аналитики для Telegram-ботов. Он легко интегрируется с существующей архитектурой проекта и предоставляет все необходимые инструменты для отслеживания и анализа взаимодействий пользователей с контентом.

Основные преимущества:
- **Комплексность**: отслеживание всех типов взаимодействий
- **Гибкость**: настраиваемые периоды и фильтры
- **Производительность**: оптимизированные запросы и возможность кэширования
- **Безопасность**: валидация данных и контроль доступа
- **Расширяемость**: легкая интеграция с внешними системами