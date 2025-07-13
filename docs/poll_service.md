# PollService - Сервис управления опросами и викторинами

## Обзор

`PollService` - это комплексный сервис для управления опросами и викторинами в Telegram боте. Он предоставляет полный функционал для создания, управления, голосования и анализа результатов различных типов опросов.

## Возможности

### Типы опросов
- **Простые опросы** - с единственным выбором
- **Опросы с множественным выбором** - можно выбрать несколько вариантов
- **Викторины** - с правильными ответами и объяснениями
- **Анонимные и именные опросы**
- **Опросы с ограничением по времени**

### Основной функционал
- Создание и редактирование опросов
- Управление вариантами ответов
- Обработка голосов пользователей
- Подсчет и анализ результатов
- Статистика по викторинам
- Автоматическое закрытие истекших опросов
- Очистка старых данных

## Архитектура

### Компоненты

```
PollService
├── Poll (основная модель опроса)
├── PollOption (варианты ответов)
├── PollVote (голоса пользователей)
└── AdminPost (связанный пост)
```

### Взаимодействие с другими сервисами
- **AdminPostService** - для создания постов с опросами
- **UserService** - для работы с пользователями
- **SchedulerService** - для автоматического закрытия опросов
- **Telegram Bot** - для отправки опросов и обработки ответов

## Установка и настройка

### Зависимости
```python
# requirements.txt
sqlalchemy[asyncio]
asyncpg
pydantic
```

### Инициализация
```python
from database.unit_of_work import UnitOfWork
from database import get_session

async with get_session() as session:
    uow = UnitOfWork(session)
    poll_service = uow.poll_service
```

## API Reference

### Создание опросов

#### `create_poll()`
Создание нового опроса

```python
async def create_poll(
    post_id: int,
    question: str,
    options: List[str],
    poll_type: PollType = PollType.SINGLE_CHOICE,
    is_anonymous: bool = True,
    allows_multiple_answers: bool = False,
    correct_option_id: Optional[int] = None,
    explanation: Optional[str] = None,
    open_period: Optional[int] = None,
    close_date: Optional[datetime] = None,
) -> Poll
```

**Параметры:**
- `post_id` - ID связанного поста
- `question` - Текст вопроса
- `options` - Список вариантов ответов
- `poll_type` - Тип опроса (SINGLE_CHOICE, MULTIPLE_CHOICE, QUIZ)
- `is_anonymous` - Анонимность опроса
- `allows_multiple_answers` - Разрешить множественный выбор
- `correct_option_id` - ID правильного ответа (для викторин)
- `explanation` - Объяснение правильного ответа
- `open_period` - Период открытия в секундах
- `close_date` - Дата закрытия опроса

#### `update_poll()`
Обновление существующего опроса

```python
async def update_poll(
    poll_id: int,
    question: Optional[str] = None,
    options: Optional[List[str]] = None,
    **kwargs
) -> Optional[Poll]
```

### Управление опросами

#### `delete_poll()`
```python
async def delete_poll(poll_id: int) -> bool
```

#### `close_poll()`
```python
async def close_poll(poll_id: int) -> Optional[Poll]
```

### Получение опросов

#### `get_poll_by_id()`
```python
async def get_poll_by_id(poll_id: int) -> Optional[Poll]
```

#### `get_active_polls()`
```python
async def get_active_polls(limit: int = 50) -> List[Poll]
```

#### `get_polls_by_type()`
```python
async def get_polls_by_type(poll_type: PollType, limit: int = 50) -> List[Poll]
```

### Голосование

#### `vote()`
Голосование в опросе

```python
async def vote(
    poll_id: int,
    user_id: int,
    option_ids: List[int]
) -> Tuple[bool, str]
```

**Возвращает:** `(успех, сообщение об ошибке)`

#### `remove_vote()`
```python
async def remove_vote(poll_id: int, user_id: int) -> bool
```

#### `get_user_vote()`
```python
async def get_user_vote(poll_id: int, user_id: int) -> Optional[List[PollVote]]
```

### Результаты и статистика

#### `get_poll_results()`
Получение результатов опроса

```python
async def get_poll_results(poll_id: int) -> Optional[Dict]
```

**Возвращает:**
```python
{
    "poll_id": 1,
    "question": "Ваш любимый язык?",
    "poll_type": "single_choice",
    "total_votes": 150,
    "is_closed": False,
    "options": [
        {
            "id": 1,
            "text": "Python",
            "votes": 75,
            "percentage": 50.0,
            "is_correct": False
        }
    ]
}
```

#### `get_quiz_results()`
Получение результатов викторины

```python
async def get_quiz_results(poll_id: int) -> Optional[Dict]
```

**Дополнительные поля для викторин:**
```python
{
    "quiz_stats": {
        "correct_answers": 45,
        "incorrect_answers": 30,
        "correct_percentage": 60.0,
        "difficulty_level": "medium"
    }
}
```

#### `get_user_quiz_score()`
Статистика пользователя по викторинам

```python
async def get_user_quiz_score(user_id: int, limit: int = 10) -> Dict
```

### Автоматические задачи

#### `close_expired_polls()`
```python
async def close_expired_polls() -> int
```

#### `cleanup_old_votes()`
```python
async def cleanup_old_votes(days: int = 90) -> int
```

## Примеры использования

### 1. Создание простого опроса

```python
async def create_simple_poll():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        poll = await uow.poll_service.create_poll(
            post_id=1,
            question="Какой ваш любимый фреймворк?",
            options=["FastAPI", "Django", "Flask", "Другой"],
            poll_type=PollType.SINGLE_CHOICE,
            is_anonymous=True
        )
        
        return poll
```

### 2. Создание викторины

```python
async def create_quiz():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        poll = await uow.poll_service.create_poll(
            post_id=2,
            question="Что означает HTTP?",
            options=[
                "HyperText Transfer Protocol",
                "High Tech Transfer Protocol",
                "Home Tool Transfer Protocol",
                "Host Transfer Protocol"
            ],
            poll_type=PollType.QUIZ,
            correct_option_id=1,
            explanation="HTTP расшифровывается как HyperText Transfer Protocol",
            close_date=datetime.now() + timedelta(hours=24)
        )
        
        return poll
```

### 3. Голосование

```python
async def vote_in_poll(poll_id: int, user_id: int):
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=user_id,
            option_ids=[1]  # Выбираем первый вариант
        )
        
        if success:
            print("Голос учтен!")
        else:
            print(f"Ошибка: {message}")
```

### 4. Получение результатов

```python
async def show_poll_results(poll_id: int):
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        results = await uow.poll_service.get_poll_results(poll_id)
        
        print(f"Опрос: {results['question']}")
        print(f"Всего голосов: {results['total_votes']}")
        
        for option in results['options']:
            print(f"{option['text']}: {option['votes']} ({option['percentage']:.1f}%)")
```

## Интеграция с Telegram Bot

### Создание опроса в боте

```python
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

@dp.message(Command("poll"))
async def create_poll_command(message: types.Message, bot: Bot):
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создаем пост
        post = await uow.admin_post_service.create_draft(
            title="Новый опрос",
            content="Участвуйте в опросе!",
            author_id=message.from_user.id
        )
        
        # Создаем опрос
        poll = await uow.poll_service.create_poll(
            post_id=post.id,
            question="Как дела?",
            options=["Отлично", "Хорошо", "Нормально", "Плохо"],
            is_anonymous=True
        )
        
        # Отправляем в Telegram
        await bot.send_poll(
            chat_id=message.chat.id,
            question=poll.question,
            options=[opt.text for opt in poll.options],
            is_anonymous=poll.is_anonymous
        )
```

### Обработка ответов

```python
@dp.poll_answer()
async def poll_answer_handler(poll_answer: types.PollAnswer, bot: Bot):
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Находим наш опрос (нужно сохранять соответствие)
        poll_id = get_poll_id_by_telegram_poll_id(poll_answer.poll_id)
        
        # Регистрируем голос
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=poll_answer.user.id,
            option_ids=poll_answer.option_ids
        )
        
        if success:
            # Показываем результаты
            results = await uow.poll_service.get_poll_results(poll_id)
            await show_results_to_user(bot, poll_answer.user.id, results)
```

### Создание викторины

```python
@dp.message(Command("quiz"))
async def create_quiz_command(message: types.Message, bot: Bot):
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создаем викторину
        poll = await uow.poll_service.create_poll(
            post_id=await create_quiz_post(),
            question="Сколько байт в килобайте?",
            options=["1000", "1024", "1048", "1200"],
            poll_type=PollType.QUIZ,
            correct_option_id=2,
            explanation="В килобайте 1024 байта (2^10)"
        )
        
        # Отправляем викторину
        await bot.send_poll(
            chat_id=message.chat.id,
            question=poll.question,
            options=[opt.text for opt in poll.options],
            type="quiz",
            correct_option_id=1,  # Telegram использует 0-based индексы
            explanation=poll.explanation
        )
```

## Структуры данных

### Poll
```python
class Poll:
    id: int
    post_id: int
    question: str
    poll_type: PollType
    is_anonymous: bool
    allows_multiple_answers: bool
    is_closed: bool
    total_voter_count: int
    correct_option_id: Optional[int]
    explanation: Optional[str]
    open_period: Optional[int]
    close_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### PollOption
```python
class PollOption:
    id: int
    poll_id: int
    text: str
    position: int
    voter_count: int
    percentage: float
```

### PollVote
```python
class PollVote:
    id: int
    poll_id: int
    option_id: int
    user_id: int
    voted_at: datetime
```

## Производительность и оптимизация

### Индексы базы данных
```sql
-- Для быстрого поиска опросов
CREATE INDEX idx_polls_post_id ON polls(post_id);
CREATE INDEX idx_polls_type_status ON polls(poll_type, is_closed);
CREATE INDEX idx_polls_close_date ON polls(close_date) WHERE close_date IS NOT NULL;

-- Для подсчета голосов
CREATE INDEX idx_poll_votes_poll_user ON poll_votes(poll_id, user_id);
CREATE INDEX idx_poll_votes_option ON poll_votes(option_id);
CREATE INDEX idx_poll_votes_voted_at ON poll_votes(voted_at);
```

### Кэширование
```python
# Кэширование результатов популярных опросов
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_poll_results(poll_id: int):
    return await poll_service.get_poll_results(poll_id)
```

### Пакетная обработка
```python
# Обновление счетчиков пакетами
async def batch_update_vote_counts(poll_ids: List[int]):
    for poll_id in poll_ids:
        await poll_service._update_vote_counts(poll_id)
```

## Безопасность

### Валидация данных
- Проверка существования опроса перед голосованием
- Валидация вариантов ответов
- Проверка прав доступа к опросу
- Ограничение на количество вариантов ответов

### Контроль доступа
```python
async def check_poll_access(poll_id: int, user_id: int) -> bool:
    poll = await poll_service.get_poll_by_id(poll_id)
    if not poll or poll.is_closed:
        return False
    
    # Дополнительные проверки доступа
    return True
```

## Мониторинг и логирование

```python
import logging

logger = logging.getLogger(__name__)

# Логирование важных событий
logger.info(f"Poll {poll_id} created by user {user_id}")
logger.info(f"User {user_id} voted in poll {poll_id}")
logger.warning(f"Attempt to vote in closed poll {poll_id}")
```

## Расширения и интеграции

### Экспорт данных
```python
async def export_poll_data(poll_id: int) -> Dict:
    """Экспорт данных опроса для анализа"""
    results = await poll_service.get_poll_results(poll_id)
    statistics = await poll_service.get_poll_statistics(poll_id)
    
    return {
        "results": results,
        "statistics": statistics,
        "export_date": datetime.now().isoformat()
    }
```

### Webhook интеграции
```python
async def send_poll_webhook(poll_id: int, event: str):
    """Отправка webhook при событиях опроса"""
    webhook_url = get_webhook_url()
    data = {
        "poll_id": poll_id,
        "event": event,
        "timestamp": datetime.now().isoformat()
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=data)
```

## Заключение

`PollService` предоставляет мощный и гибкий инструмент для работы с опросами и викторинами в Telegram боте. Сервис поддерживает различные типы опросов, обеспечивает надежную обработку голосов и предоставляет детальную аналитику результатов.

Основные преимущества:
- Полная поддержка всех типов опросов Telegram
- Гибкая система настроек и ограничений
- Детальная аналитика и статистика
- Автоматическое управление жизненным циклом опросов
- Простая интеграция с существующим кодом бота
- Высокая производительность и масштабируемость