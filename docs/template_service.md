# TemplateService Documentation

## Обзор

`TemplateService` - это сервис для управления шаблонами постов в Telegram боте. Он позволяет создавать, редактировать, удалять и использовать шаблоны для быстрого создания постов с предустановленным контентом.

## Возможности

### Основные функции
- **Создание шаблонов** - создание новых шаблонов с различными типами контента
- **Управление шаблонами** - редактирование, удаление, дублирование
- **Использование шаблонов** - создание постов на основе существующих шаблонов
- **Категоризация** - организация шаблонов по категориям
- **Поиск и фильтрация** - быстрый поиск нужных шаблонов
- **Экспорт/импорт** - сохранение и загрузка шаблонов
- **Статистика** - аналитика использования шаблонов

### Типы шаблонов
- **Текстовые** - простые текстовые сообщения
- **С медиа** - шаблоны с изображениями, видео, документами
- **С плейсхолдерами** - шаблоны с заменяемыми переменными
- **Категоризированные** - шаблоны, организованные по темам

## Архитектура

### Компоненты

```
TemplateService
├── Создание и управление
│   ├── create_template()
│   ├── update_template()
│   ├── delete_template()
│   └── duplicate_template()
├── Получение шаблонов
│   ├── get_template_by_id()
│   ├── get_template_by_name()
│   ├── get_user_templates()
│   └── get_templates_count()
├── Использование
│   └── create_post_from_template()
├── Поиск и рекомендации
│   ├── search_templates()
│   └── get_recommended_templates()
├── Категории и статистика
│   ├── get_template_categories()
│   └── get_template_statistics()
└── Экспорт/импорт
    ├── export_template()
    └── import_template()
```

### Взаимодействие с другими сервисами
- **AdminPostService** - создание постов из шаблонов
- **Repository** - работа с базой данных
- **NotificationService** - уведомления о создании/использовании шаблонов

## Установка

### Требования
- Python 3.8+
- SQLAlchemy 2.0+
- asyncpg
- loguru

### Интеграция

1. Добавьте поля шаблона в модель `AdminPost`:
```python
is_template = Column(Boolean, default=False, nullable=False)
template_name = Column(String(255), nullable=True)
template_description = Column(Text, nullable=True)
```

2. Импортируйте сервис:
```python
from database.services.template_service import TemplateService
```

3. Инициализируйте в `UnitOfWork`:
```python
self.template_service = TemplateService(session, self.repository)
```

## API Reference

### Создание и управление шаблонами

#### `create_template()`
Создание нового шаблона поста.

```python
async def create_template(
    title: str,
    content: str,
    template_name: str,
    created_by: int,
    template_description: Optional[str] = None,
    media_type: Optional[MediaType] = None,
    media_file_id: Optional[str] = None,
    media_caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    links: Optional[List[Dict[str, str]]] = None,
    categories: Optional[List[str]] = None,
) -> AdminPost
```

**Параметры:**
- `title` - заголовок шаблона
- `content` - содержимое шаблона
- `template_name` - уникальное имя шаблона
- `created_by` - ID создателя
- `template_description` - описание шаблона
- `media_type` - тип медиа (фото, видео, документ)
- `media_file_id` - ID медиа файла в Telegram
- `media_caption` - подпись к медиа
- `hashtags` - список хештегов
- `links` - список ссылок
- `categories` - список категорий

**Возвращает:** объект `AdminPost` с `is_template=True`

**Исключения:**
- `ValueError` - если шаблон с таким именем уже существует

#### `update_template()`
Обновление существующего шаблона.

```python
async def update_template(
    template_id: int,
    user_id: int,
    **kwargs
) -> AdminPost
```

#### `delete_template()`
Удаление шаблона.

```python
async def delete_template(
    template_id: int,
    user_id: int
) -> bool
```

#### `duplicate_template()`
Дублирование шаблона с новым именем.

```python
async def duplicate_template(
    template_id: int,
    user_id: int,
    new_template_name: str
) -> AdminPost
```

### Получение шаблонов

#### `get_user_templates()`
Получение списка шаблонов пользователя с фильтрацией и сортировкой.

```python
async def get_user_templates(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> List[AdminPost]
```

**Параметры:**
- `user_id` - ID пользователя
- `limit` - максимальное количество результатов
- `offset` - смещение для пагинации
- `search` - поисковый запрос
- `category` - фильтр по категории
- `sort_by` - поле для сортировки
- `sort_order` - порядок сортировки (asc/desc)

#### `get_template_by_name()`
Получение шаблона по имени.

```python
async def get_template_by_name(
    template_name: str,
    user_id: int
) -> Optional[AdminPost]
```

### Использование шаблонов

#### `create_post_from_template()`
Создание поста на основе шаблона.

```python
async def create_post_from_template(
    template_id: int,
    user_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    target_groups: Optional[List[int]] = None,
    scheduled_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    priority: int = 0,
    override_media: bool = False,
    new_media_type: Optional[MediaType] = None,
    new_media_file_id: Optional[str] = None,
    new_media_caption: Optional[str] = None,
    additional_hashtags: Optional[List[str]] = None,
    additional_links: Optional[List[Dict[str, str]]] = None,
    additional_categories: Optional[List[str]] = None,
) -> AdminPost
```

**Особенности:**
- Создает новый пост с `is_template=False`
- Копирует все данные из шаблона
- Позволяет переопределить любые поля
- Объединяет хештеги и категории
- Поддерживает планирование публикации

### Поиск и рекомендации

#### `search_templates()`
Расширенный поиск по шаблонам.

```python
async def search_templates(
    user_id: int,
    query: str,
    limit: int = 20,
    include_content: bool = True,
) -> List[AdminPost]
```

**Поиск выполняется по:**
- Названию шаблона
- Описанию
- Заголовку
- Содержимому (опционально)
- Хештегам
- Категориям

#### `get_recommended_templates()`
Получение рекомендованных шаблонов на основе категорий.

```python
async def get_recommended_templates(
    user_id: int,
    based_on_categories: List[str],
    limit: int = 5
) -> List[AdminPost]
```

### Категории и статистика

#### `get_template_categories()`
Получение списка всех категорий шаблонов пользователя.

```python
async def get_template_categories(
    user_id: int
) -> List[str]
```

#### `get_template_statistics()`
Получение статистики по шаблонам.

```python
async def get_template_statistics(
    user_id: int
) -> Dict[str, Any]
```

**Возвращает:**
```python
{
    "total_templates": int,
    "categories_count": int,
    "category_distribution": Dict[str, int],
    "media_type_distribution": Dict[str, int],
    "most_recent": str  # ISO datetime
}
```

### Экспорт и импорт

#### `export_template()`
Экспорт шаблона в JSON формат.

```python
async def export_template(
    template_id: int,
    user_id: int
) -> Dict[str, Any]
```

**Формат экспорта:**
```json
{
    "template_name": "string",
    "template_description": "string",
    "title": "string",
    "content": "string",
    "media_type": "string",
    "media_caption": "string",
    "hashtags": ["string"],
    "links": [{"url": "string", "text": "string"}],
    "categories": ["string"],
    "exported_at": "ISO datetime",
    "version": "1.0"
}
```

#### `import_template()`
Импорт шаблона из JSON формата.

```python
async def import_template(
    template_data: Dict[str, Any],
    user_id: int
) -> AdminPost
```

**Особенности:**
- Автоматически разрешает конфликты имен
- Валидирует обязательные поля
- Поддерживает версионность формата

## Примеры использования

### Создание простого шаблона

```python
async def create_simple_template():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        template = await uow.template_service.create_template(
            title="Ежедневная сводка",
            content="📰 Новости за {date}\n\n{content}\n\n#новости",
            template_name="daily_news",
            template_description="Шаблон для ежедневных новостей",
            created_by=123456789,
            categories=["Новости"]
        )
        
        await session.commit()
        return template
```

### Создание поста из шаблона

```python
async def use_template():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Получаем шаблон
        template = await uow.template_service.get_template_by_name(
            "daily_news", 123456789
        )
        
        # Создаем пост с заменой плейсхолдеров
        content = template.content.replace(
            "{date}", "15 декабря 2024"
        ).replace(
            "{content}", "Важные события дня..."
        )
        
        post = await uow.template_service.create_post_from_template(
            template_id=template.id,
            user_id=123456789,
            content=content,
            target_groups=[1001, 1002],
            scheduled_at=datetime.now() + timedelta(hours=1)
        )
        
        await session.commit()
        return post
```

### Поиск и фильтрация

```python
async def search_templates():
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Поиск по ключевому слову
        results = await uow.template_service.search_templates(
            user_id=123456789,
            query="новости",
            limit=10
        )
        
        # Фильтрация по категории
        news_templates = await uow.template_service.get_user_templates(
            user_id=123456789,
            category="Новости",
            sort_by="updated_at",
            sort_order="desc"
        )
        
        return results, news_templates
```

## Интеграция с Telegram Bot

### Команды бота

```python
# Создание шаблона
@dp.message_handler(commands=['create_template'])
async def create_template_command(message: types.Message):
    # Логика создания шаблона
    pass

# Список шаблонов
@dp.message_handler(commands=['templates'])
async def list_templates_command(message: types.Message):
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        templates = await uow.template_service.get_user_templates(
            user_id=message.from_user.id,
            limit=10
        )
        
        if not templates:
            await message.reply("📝 У вас пока нет шаблонов")
            return
        
        response = "📋 Ваши шаблоны:\n\n"
        for template in templates:
            response += f"• {template.template_name}\n"
            response += f"  {template.title}\n\n"
        
        await message.reply(response)

# Использование шаблона
@dp.message_handler(commands=['use_template'])
async def use_template_command(message: types.Message):
    # Логика использования шаблона
    pass
```

### Inline клавиатуры

```python
def get_templates_keyboard(templates: List[AdminPost]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    
    for template in templates:
        keyboard.add(
            InlineKeyboardButton(
                text=template.template_name,
                callback_data=f"use_template:{template.id}"
            )
        )
    
    return keyboard

@dp.callback_query_handler(lambda c: c.data.startswith('use_template:'))
async def use_template_callback(callback_query: types.CallbackQuery):
    template_id = int(callback_query.data.split(':')[1])
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        post = await uow.template_service.create_post_from_template(
            template_id=template_id,
            user_id=callback_query.from_user.id,
            target_groups=[1001]  # Группы по умолчанию
        )
        
        await session.commit()
        await callback_query.answer("✅ Пост создан из шаблона!")
```

## Структуры данных

### Модель шаблона

```python
class AdminPost(Base):
    # Основные поля
    id: int
    title: str
    content: str
    
    # Поля шаблона
    is_template: bool = False
    template_name: Optional[str] = None
    template_description: Optional[str] = None
    
    # Медиа
    media_type: Optional[MediaType] = None
    media_file_id: Optional[str] = None
    media_caption: Optional[str] = None
    
    # Метаданные
    hashtags: List[str] = []
    links: List[Dict[str, str]] = []
    categories: List[str] = []
    
    # Системные поля
    created_by: int
    created_at: datetime
    updated_at: datetime
```

### Формат экспорта

```python
{
    "template_name": "daily_news",
    "template_description": "Шаблон для ежедневных новостей",
    "title": "Ежедневная сводка",
    "content": "📰 Новости за {date}\n\n{content}\n\n#новости",
    "media_type": null,
    "media_caption": null,
    "hashtags": ["новости", "сводка"],
    "links": [],
    "categories": ["Новости"],
    "exported_at": "2024-12-15T10:30:00Z",
    "version": "1.0"
}
```

## Конфигурация

### Настройки по умолчанию

```python
# Лимиты
MAX_TEMPLATES_PER_USER = 100
MAX_TEMPLATE_NAME_LENGTH = 255
MAX_TEMPLATE_DESCRIPTION_LENGTH = 1000

# Поиск
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 100

# Экспорт
EXPORT_VERSION = "1.0"
SUPPORTED_IMPORT_VERSIONS = ["1.0"]
```

### Переменные окружения

```bash
# Опционально
TEMPLATE_CACHE_TTL=3600  # Время кеширования в секундах
TEMPLATE_SEARCH_TIMEOUT=30  # Таймаут поиска в секундах
```

## Производительность

### Оптимизации

1. **Индексы базы данных:**
```sql
CREATE INDEX idx_admin_posts_template ON admin_posts(is_template, created_by);
CREATE INDEX idx_admin_posts_template_name ON admin_posts(template_name, created_by);
CREATE INDEX idx_admin_posts_categories ON admin_posts USING GIN(categories);
```

2. **Кеширование:**
- Кеширование часто используемых шаблонов
- Кеширование результатов поиска
- Кеширование статистики

3. **Пагинация:**
- Использование LIMIT/OFFSET для больших списков
- Курсорная пагинация для лучшей производительности

### Мониторинг

```python
# Метрики для отслеживания
- template_creation_count
- template_usage_count
- search_query_duration
- export_import_operations
```

## Безопасность

### Проверки доступа

1. **Владение шаблоном:**
```python
# Все операции проверяют created_by
template = await self._get_template_by_id(template_id, user_id)
if not template:
    raise ValueError("Шаблон не найден")
```

2. **Валидация данных:**
```python
# Проверка уникальности имен
# Валидация длины полей
# Санитизация контента
```

3. **Ограничения:**
```python
# Лимит количества шаблонов на пользователя
# Ограничение размера контента
# Проверка прав на медиа файлы
```

## Логирование

### События для логирования

```python
# Создание/изменение
logger.info(f"Создан шаблон '{template_name}' пользователем {user_id}")
logger.info(f"Обновлен шаблон {template_id}")
logger.info(f"Удален шаблон {template_id}")

# Использование
logger.info(f"Создан пост из шаблона '{template_name}'")
logger.info(f"Экспортирован шаблон {template_id}")
logger.info(f"Импортирован шаблон '{template_name}'")

# Ошибки
logger.error(f"Ошибка создания шаблона: {error}")
logger.warning(f"Попытка доступа к чужому шаблону: user={user_id}, template={template_id}")
```

## Расширения

### Возможные улучшения

1. **Версионирование шаблонов:**
```python
# Сохранение истории изменений
# Откат к предыдущим версиям
# Сравнение версий
```

2. **Совместное использование:**
```python
# Публичные шаблоны
# Шаблоны команды
# Импорт из библиотеки
```

3. **Расширенные плейсхолдеры:**
```python
# Динамические переменные
# Условная логика
# Форматирование данных
```

4. **AI-помощник:**
```python
# Генерация шаблонов
# Предложения улучшений
# Автоматическая категоризация
```

5. **Аналитика использования:**
```python
# Популярность шаблонов
# Эффективность постов
# Рекомендации оптимизации
```

## Миграции

### Добавление полей шаблона

```python
# Alembic migration
def upgrade():
    op.add_column('admin_posts', sa.Column('is_template', sa.Boolean(), nullable=False, default=False))
    op.add_column('admin_posts', sa.Column('template_name', sa.String(255), nullable=True))
    op.add_column('admin_posts', sa.Column('template_description', sa.Text(), nullable=True))
    
    # Индексы
    op.create_index('idx_admin_posts_template', 'admin_posts', ['is_template', 'created_by'])
    op.create_index('idx_admin_posts_template_name', 'admin_posts', ['template_name', 'created_by'])

def downgrade():
    op.drop_index('idx_admin_posts_template_name')
    op.drop_index('idx_admin_posts_template')
    op.drop_column('admin_posts', 'template_description')
    op.drop_column('admin_posts', 'template_name')
    op.drop_column('admin_posts', 'is_template')
```

## Заключение

`TemplateService` предоставляет мощный и гибкий инструмент для управления шаблонами постов. Он интегрируется с существующей архитектурой проекта и предоставляет все необходимые функции для эффективной работы с шаблонами в Telegram боте.

Основные преимущества:
- **Переиспользование контента** - быстрое создание постов
- **Организация** - категоризация и поиск шаблонов
- **Гибкость** - поддержка различных типов контента
- **Безопасность** - контроль доступа и валидация
- **Масштабируемость** - оптимизация для больших объемов данных