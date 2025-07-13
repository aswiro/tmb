# settings.py - настройки приложения
"""
Модуль содержит настройки для подключения к базе данных PostgreSQL.

Настройки загружаются из переменных окружения с использованием pydantic-settings.
Значения по умолчанию используются, если переменные окружения не заданы.

Пример использования:
    from config.settings import settings

    print(f"Подключение к базе данных: {settings.database_url}")
    print(f"Размер пула соединений: {settings.pool_size}")
"""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения.

    Класс использует pydantic-settings для загрузки настроек из переменных окружения.
    Если переменные окружения не заданы, используются значения по умолчанию.

    Пример использования:
        from config.settings import settings

        # Доступ к настройкам базы данных
        engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_timeout=settings.pool_timeout,
            pool_recycle=settings.pool_recycle,
        )

        # Доступ к токену Telegram бота
        bot = Bot(token=settings.telegram_bot_token.get_secret_value())
    """

    # Telegram settings
    telegram_bot_token: SecretStr = Field(
        default="", description="Токен Telegram бота", env="TELEGRAM_BOT_TOKEN"
    )

    # Database settings
    db_user: str = Field(
        default="postgres", description="Имя пользователя базы данных", env="DB_USER"
    )
    db_password: SecretStr = Field(
        default="postgres",
        description="Пароль пользователя базы данных",
        env="DB_PASSWORD",
    )
    db_host: str = Field(
        default="localhost", description="Хост базы данных", env="DB_HOST"
    )
    db_port: int = Field(default=5432, description="Порт базы данных", env="DB_PORT")
    db_name: str = Field(
        default="app_db", description="Название базы данных", env="DB_NAME"
    )
    database_echo: bool = Field(
        default=False,
        description="Включить вывод SQL запросов в консоль",
        env="DATABASE_ECHO",
    )
    database_url: str = Field(
        default="",
        description="URL для подключения к базе данных, формируется автоматически",
    )

    # Настройки пула соединений
    pool_size: int = Field(
        default=20, description="Размер пула соединений", env="DB_POOL_SIZE"
    )
    max_overflow: int = Field(
        default=30,
        description="Максимальное количество дополнительных соединений",
        env="DB_MAX_OVERFLOW",
    )
    pool_timeout: int = Field(
        default=30,
        description="Таймаут ожидания соединения в секундах",
        env="DB_POOL_TIMEOUT",
    )
    pool_recycle: int = Field(
        default=3600,
        description="Время жизни соединения в секундах",
        env="DB_POOL_RECYCLE",
    )

    # Настройки производительности
    query_timeout: int = Field(
        default=60,
        description="Таймаут выполнения запроса в секундах",
        env="DB_QUERY_TIMEOUT",
    )
    slow_query_threshold: float = Field(
        default=1.0,
        description="Порог для определения медленных запросов в секундах",
        env="DB_SLOW_QUERY_THRESHOLD",
    )

    # Redis settings
    redis_host: str = Field(
        default="localhost", description="Хост Redis", env="REDIS_HOST"
    )
    redis_port: int = Field(default=6379, description="Порт Redis", env="REDIS_PORT")
    redis_password: SecretStr | None = Field(
        default=None, description="Пароль Redis", env="REDIS_PASSWORD"
    )
    redis_db: int = Field(
        default=0, description="Номер базы данных Redis", env="REDIS_DB"
    )
    redis_url: str = Field(
        default="",
        description="URL для подключения к Redis, формируется автоматически",
    )

    # Cache settings
    cache_ttl: int = Field(default=3600, description="TTL для кэша", env="CACHE_TTL")
    user_cache_ttl: int = Field(
        default=1800, description="TTL для кэша пользователей", env="USER_CACHE_TTL"
    )

    # Bot administration settings
    bot_admin_ids: list[int] = Field(
        default_factory=list, description="Список ID администраторов бота"
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        validate_default=True,
        env_file=".env",
        extra="ignore",
    )

    def model_post_init(self, __context) -> None:
        """
        Автоматическое формирование URL для подключения к базе данных и Redis после инициализации.

        Этот метод вызывается автоматически после создания экземпляра класса.
        Он формирует URL для подключения к базе данных и Redis на основе отдельных параметров,
        если URL не были заданы явно.
        """
        # Формирование URL для базы данных
        if not self.database_url:
            self.database_url = f"postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"

        # Формирование URL для Redis
        if not self.redis_url:
            password = (
                self.redis_password.get_secret_value().strip()
                if self.redis_password
                else None
            )
            if password:
                self.redis_url = f"redis://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            else:
                self.redis_url = (
                    f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
                )


# Initialize settings
settings = Settings()


# Пример использования в Telegram боте
"""
from aiogram import Bot, Dispatcher
from database import database, UserRepository

async def start_handler(message):
    async with database.get_session() as session:
        user_repo = UserRepository(session)

        # Создаем или обновляем пользователя
        user = await user_repo.get_by_id(message.from_user.id)
        if not user:
            user = await user_repo.create(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code
            )

        await message.reply(f"Привет, {user.full_name}!")

# Инициализация при запуске бота
async def on_startup():
    await database.initialize()
    await database.init_db()

async def on_shutdown():
    await database.close()
"""
