# database/db_main.py
import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from config.settings import settings
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool


logger = logging.getLogger(__name__)


class Database:
    """Оптимизированный менеджер подключений к базе данных"""

    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.async_session_factory: async_sessionmaker | None = None
        self.Base = declarative_base()
        self._is_initialized = False

    async def initialize(self):
        """Инициализация подключения к БД"""
        if self._is_initialized:
            return

        # Настройки подключения для PostgreSQL
        connect_args = {
            "server_settings": {
                "application_name": "telegram_bot",
                "jit": "off"  # Отключить JIT для стабильности
            },
            "command_timeout": 60,  # Таймаут команд
        }

        # Создание движка с оптимизированными настройками
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,  # Логирование SQL только в режиме отладки
            pool_pre_ping=True,  # Проверка соединений перед использованием
            pool_recycle=3600,  # Пересоздание соединений каждый час
            pool_size=20,  # Базовый размер пула
            max_overflow=30,  # Максимальные дополнительные соединения
            pool_timeout=30,  # Таймаут получения соединения из пула
            poolclass=QueuePool,  # Явно указать тип пула
            connect_args=connect_args,
            # Дополнительные настройки для production
            future=True,
            execution_options={"isolation_level": "READ_COMMITTED"},
        )

        # Создание фабрики сессий
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        # Настройка событий для мониторинга
        self._setup_engine_events()

        self._is_initialized = True
        logger.info("Database connection initialized successfully")

    def _setup_engine_events(self):
        """Настройка событий движка для мониторинга"""

        @event.listens_for(self.engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
            """Настройка соединения (пример для SQLite, адаптировать под PostgreSQL)"""
            if "sqlite" in settings.database_url:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn,  # noqa: ARG001
            cursor,  # noqa: ARG001
            statement,  # noqa: ARG001
            parameters,  # noqa: ARG001
            context,
            executemany,  # noqa: ARG001
        ):
            """Логирование медленных запросов"""
            context._query_start_time = asyncio.get_event_loop().time()

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn,  # noqa: ARG001
            cursor,  # noqa: ARG001
            statement,
            parameters,  # noqa: ARG001
            context,
            executemany,  # noqa: ARG001
        ):
            """Завершение мониторинга запросов"""
            total = asyncio.get_event_loop().time() - context._query_start_time
            if total > 1.0:  # Логировать запросы длительнее 1 секунды
                logger.warning(
                    f"Slow query detected: {total:.2f}s - {statement[:100]}..."
                )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Контекстный менеджер для получения сессии БД

        Usage:
            async with db.get_session() as session:
                result = await session.execute(query)
        """
        if not self._is_initialized:
            await self.initialize()

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_session_dependency(self) -> AsyncSession:
        """
        Dependency injection для FastAPI/других фреймворков

        Usage:
            async def handler(db: AsyncSession = Depends(database.get_session_dependency)):
                pass
        """
        if not self._is_initialized:
            await self.initialize()
        return self.async_session_factory()

    async def health_check(self) -> dict[str, Any]:
        """
        Проверка здоровья базы данных

        Returns:
            dict: Статус здоровья и метрики
        """
        try:
            async with self.get_session() as session:
                # Простой запрос для проверки соединения
                result = await session.execute(text("SELECT 1 as health_check"))
                result.fetchone()

                # Получение статистики пула
                pool_status = await self.get_pool_status()

                return {
                    "status": "healthy",
                    "database": "connected",
                    "pool": pool_status,
                    "timestamp": asyncio.get_event_loop().time(),
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            }

    async def get_pool_status(self) -> dict[str, int]:
        """
        Получение статистики пула соединений

        Returns:
            dict: Метрики пула соединений
        """
        if not self.engine:
            return {"error": "Engine not initialized"}

        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalidated(),
        }

    async def execute_raw_sql(self, query: str, params: dict[str, Any] = None) -> Any:
        """
        Выполнение сырого SQL запроса

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            Результат выполнения запроса
        """
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result

    async def init_db(self):
        """Создание таблиц базы данных"""
        if not self._is_initialized:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def drop_all_tables(self):
        """Удаление всех таблиц (осторожно!)"""
        if not self._is_initialized:
            await self.initialize()

        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.drop_all)
        logger.warning("All database tables dropped")

    async def vacuum_analyze(self):
        """Запуск VACUUM ANALYZE для PostgreSQL"""
        try:
            async with self.get_session() as session:
                await session.execute(text("VACUUM ANALYZE"))
            logger.info("VACUUM ANALYZE completed successfully")
        except Exception as e:
            logger.error(f"VACUUM ANALYZE failed: {e}")

    async def get_table_sizes(self) -> dict[str, int]:
        """Получение размеров таблиц (PostgreSQL)"""
        query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """

        try:
            result = await self.execute_raw_sql(query)
            return {row.tablename: row.bytes for row in result.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get table sizes: {e}")
            return {}

    async def close(self):
        """Закрытие всех соединений с базой данных"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
        self._is_initialized = False

    async def __aenter__(self):
        """Async context manager enter"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Пример использования с context manager
"""
Usage examples:

1. Basic usage:
    async with database.get_session() as session:
        user = await session.get(User, user_id)

2. Health check:
    health = await database.health_check()

3. Raw SQL:
    result = await database.execute_raw_sql(
        "SELECT COUNT(*) FROM users WHERE created_at > :date",
        {"date": datetime.now() - timedelta(days=7)}
    )

4. Application lifecycle:
    # At startup
    await init_database()

    # At shutdown
    await close_database()
"""
