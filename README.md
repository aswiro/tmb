# TMB (Telegram Management Bot)

Полнофункциональный бот для управления группами в Telegram с поддержкой аналитики, рекламы, модерации и автоматизации.

## Возможности

- 📊 Аналитика постов и активности
- 🎯 Система рекламы и объявлений
- 🛡️ Модерация и фильтрация контента
- 🤖 Автоматизация задач
- 📝 Шаблоны постов
- 🗳️ Опросы и голосования
- 🔔 Уведомления
- 🌐 Мультиязычность (RU/EN)

## Технологии

- Python 3.12
- aiogram (Telegram Bot API)
- SQLAlchemy 2.0 + asyncpg
- Redis
- Alembic (миграции)
- uv (управление зависимостями)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/aswiro/tmb.git
cd tmb
```

2. Установите зависимости:
```bash
uv sync
```

3. Настройте переменные окружения в `.env`

4. Запустите миграции:
```bash
alembic upgrade head
```

5. Запустите бота:
```bash
python main.py
```

## Документация

Подробная документация находится в папке `docs/`:

- [Архитектура админ-постов](docs/admin_posts_architecture.md)
- [Система рекламы](docs/ads.md)
- [Сервис уведомлений](docs/notification_service.md)
- [Аналитика постов](docs/post_analytics_service.md)
- [Планировщик](docs/scheduler_service.md)
- [Шаблоны](docs/template_service.md)
- [Интернационализация](docs/I18N_README.md)

## Лицензия

MIT License