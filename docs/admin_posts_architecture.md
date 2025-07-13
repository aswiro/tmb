# Архитектура системы постов администратора

## Обзор

Данный документ описывает рекомендуемую архитектуру для системы управления постами администратора в Telegram боте.

## Структура базы данных

### Таблица `admin_posts`

```sql
CREATE TABLE admin_posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    media_type VARCHAR(50), -- 'photo', 'video', 'document', 'animation'
    media_file_id VARCHAR(255), -- Telegram file_id
    media_caption TEXT,
    hashtags TEXT[], -- Массив хештегов
    links JSONB, -- Массив ссылок с описанием
    target_groups INTEGER[], -- ID групп для публикации
    categories VARCHAR(100)[], -- Категории поста
    scheduled_at TIMESTAMP, -- Время запланированной публикации
    published_at TIMESTAMP, -- Время фактической публикации
    expires_at TIMESTAMP, -- Время окончания показа
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'scheduled', 'published', 'expired', 'cancelled'
    priority INTEGER DEFAULT 0, -- Приоритет показа
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `post_analytics`

```sql
CREATE TABLE post_analytics (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES admin_posts(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id),
    views_count INTEGER DEFAULT 0,
    clicks_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    reactions JSONB, -- {'like': 10, 'dislike': 2, 'heart': 5}
    view_duration INTEGER, -- Среднее время просмотра в секундах
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Рекомендации по публикации

### Публикация через бота (рекомендуется)

**Преимущества:**
- Полный контроль над процессом публикации
- Интегрированная аналитика
- Единая система управления
- Возможность A/B тестирования
- Автоматическое планирование
- Централизованное логирование

**Недостатки:**
- Необходимость разработки дополнительного функционала
- Зависимость от стабильности бота

### Публикация через Telegraf

**Преимущества:**
- Готовое решение
- Надежность платформы Telegram

**Недостатки:**
- Ограниченная аналитика
- Сложность интеграции с существующей системой
- Меньше контроля над процессом

## Архитектура системы

### Компоненты

1. **PostService** - Основной сервис для работы с постами
2. **SchedulerService** - Планировщик публикаций
3. **AnalyticsService** - Сбор и анализ метрик
4. **MediaService** - Управление медиафайлами

### Структура файлов

```
database/
├── models/
│   ├── admin_post.py
│   └── post_analytics.py
├── services/
│   ├── post_service.py
│   ├── scheduler_service.py
│   ├── analytics_service.py
│   └── media_service.py
handlers/
├── admin_posts.py
keyboards/
├── admin_posts.py
```

## Модели данных

### AdminPost

```python
class AdminPost(Base):
    __tablename__ = "admin_posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    media_type: Mapped[Optional[str]] = mapped_column(String(50))
    media_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    media_caption: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String))
    links: Mapped[Optional[dict]] = mapped_column(JSON)
    target_groups: Mapped[Optional[list[int]]] = mapped_column(ARRAY(Integer))
    categories: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(100)))
    scheduled_at: Mapped[Optional[datetime]]
    published_at: Mapped[Optional[datetime]]
    expires_at: Mapped[Optional[datetime]]
    status: Mapped[str] = mapped_column(String(50), default="draft")
    priority: Mapped[int] = mapped_column(default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

### PostAnalytics

```python
class PostAnalytics(Base):
    __tablename__ = "post_analytics"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("admin_posts.id", ondelete="CASCADE"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    views_count: Mapped[int] = mapped_column(default=0)
    clicks_count: Mapped[int] = mapped_column(default=0)
    shares_count: Mapped[int] = mapped_column(default=0)
    reactions: Mapped[Optional[dict]] = mapped_column(JSON)
    view_duration: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

## Сервисы

### PostService

```python
class PostService:
    async def create_post(self, post_data: dict) -> AdminPost
    async def update_post(self, post_id: int, updates: dict) -> AdminPost
    async def delete_post(self, post_id: int) -> bool
    async def get_post(self, post_id: int) -> AdminPost
    async def get_posts_by_status(self, status: str) -> list[AdminPost]
    async def schedule_post(self, post_id: int, scheduled_at: datetime) -> bool
    async def publish_post(self, post_id: int) -> bool
    async def cancel_post(self, post_id: int) -> bool
```

### SchedulerService

```python
class SchedulerService:
    async def check_scheduled_posts(self) -> None
    async def publish_scheduled_post(self, post: AdminPost) -> bool
    async def expire_posts(self) -> None
    async def get_next_scheduled_posts(self, limit: int = 10) -> list[AdminPost]
```

### AnalyticsService

```python
class AnalyticsService:
    async def track_view(self, post_id: int, group_id: int) -> None
    async def track_click(self, post_id: int, group_id: int) -> None
    async def track_share(self, post_id: int, group_id: int) -> None
    async def track_reaction(self, post_id: int, group_id: int, reaction: str) -> None
    async def get_post_analytics(self, post_id: int) -> dict
    async def get_analytics_summary(self, date_from: date, date_to: date) -> dict
```

## Функциональность

### Основные возможности

1. **Создание постов**
   - Текстовый контент
   - Медиафайлы (фото, видео, документы)
   - Хештеги и ссылки
   - Выбор целевых групп
   - Категоризация

2. **Планирование публикаций**
   - Отложенная публикация
   - Автоматическое истечение
   - Приоритизация

3. **Аналитика**
   - Просмотры и клики
   - Реакции пользователей
   - Время просмотра
   - Статистика по группам

4. **Управление**
   - Редактирование черновиков
   - Отмена запланированных постов
   - Архивирование

### Клавиатуры и интерфейс

```python
# keyboards/admin_posts.py
def get_posts_management_keyboard():
    """Главное меню управления постами"""
    
def get_post_actions_keyboard(post_id: int):
    """Действия с конкретным постом"""
    
def get_scheduling_keyboard():
    """Планирование публикации"""
    
def get_analytics_keyboard(post_id: int):
    """Просмотр аналитики поста"""
```

### Обработчики

```python
# handlers/admin_posts.py
async def posts_menu_handler(callback: CallbackQuery):
    """Главное меню постов"""
    
async def create_post_handler(callback: CallbackQuery):
    """Создание нового поста"""
    
async def edit_post_handler(callback: CallbackQuery):
    """Редактирование поста"""
    
async def schedule_post_handler(callback: CallbackQuery):
    """Планирование публикации"""
    
async def view_analytics_handler(callback: CallbackQuery):
    """Просмотр аналитики"""
```

## Миграции

### Создание таблиц

```python
# alembic/versions/xxx_add_admin_posts.py
def upgrade():
    # Создание таблицы admin_posts
    op.create_table(
        'admin_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        # ... остальные поля
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание таблицы post_analytics
    op.create_table(
        'post_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        # ... остальные поля
        sa.ForeignKeyConstraint(['post_id'], ['admin_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
```

## Заключение

Рекомендуется реализовать публикацию постов через бота для максимального контроля и интеграции с существующей системой. Это обеспечит лучшую аналитику, гибкость в управлении и единообразие архитектуры проекта.