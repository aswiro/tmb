# db_main.py - основной модуль для работы с базой данных
"""Основной модуль для работы с базой данных.

Этот модуль содержит класс Database, который управляет подключением к базе данных,
создает таблицы и предоставляет сессии для работы с данными.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config.settings import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


class Database:
    """Класс для управления подключением к базе данных.
    
    Предоставляет методы для:
    - Инициализации подключения
    - Создания таблиц
    - Получения сессий
    - Закрытия подключения
    """
    
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Инициализирует подключение к базе данных."""
        if self._initialized:
            logger.warning("База данных уже инициализирована")
            return
            
        try:
            # Создаем движок базы данных
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.database_echo,
                pool_size=settings.pool_size,
                max_overflow=settings.max_overflow,
                pool_timeout=settings.pool_timeout,
                pool_recycle=settings.pool_recycle,
                # Дополнительные настройки для PostgreSQL
                connect_args={
                    "command_timeout": settings.query_timeout,
                    "server_settings": {
                        "jit": "off",  # Отключаем JIT для стабильности
                    },
                },
            )
            
            # Создаем фабрику сессий
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            # Проверяем подключение
            await self._check_connection()
            
            self._initialized = True
            logger.info("База данных успешно инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise
    
    async def _check_connection(self) -> None:
        """Проверяет подключение к базе данных."""
        if not self.engine:
            raise RuntimeError("Движок базы данных не инициализирован")
            
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
            logger.info("Подключение к базе данных успешно")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise
    
    async def create_tables(self) -> None:
        """Создает все таблицы в базе данных."""
        if not self.engine:
            raise RuntimeError("База данных не инициализирована")
            
        try:
            # Импортируем все модели, чтобы они были зарегистрированы
            from .models import *  # noqa: F403, F401
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Таблицы базы данных созданы")
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Удаляет все таблицы из базы данных."""
        if not self.engine:
            raise RuntimeError("База данных не инициализирована")
            
        try:
            # Импортируем все модели
            from .models import *  # noqa: F403, F401
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("Таблицы базы данных удалены")
        except Exception as e:
            logger.error(f"Ошибка при удалении таблиц: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Возвращает сессию базы данных в контекстном менеджере.
        
        Yields:
            AsyncSession: Сессия для работы с базой данных
            
        Raises:
            RuntimeError: Если база данных не инициализирована
        """
        if not self.session_factory:
            raise RuntimeError("База данных не инициализирована")
            
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка в сессии базы данных: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Закрывает подключение к базе данных."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Подключение к базе данных закрыто")
        
        self._initialized = False
        self.engine = None
        self.session_factory = None
    
    async def init_db(self) -> None:
        """Полная инициализация базы данных: подключение + создание таблиц."""
        await self.initialize()
        await self.create_tables()
        logger.info("База данных полностью инициализирована")
    
    @property
    def is_initialized(self) -> bool:
        """Проверяет, инициализирована ли база данных."""
        return self._initialized


# Глобальный экземпляр базы данных
database = Database()


# Функции для удобства использования
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Функция-зависимость для получения сессии базы данных.
    
    Используется в FastAPI и других местах, где нужна сессия.
    """
    async with database.get_session() as session:
        yield session


async def init_database() -> None:
    """Инициализирует базу данных при запуске приложения."""
    await database.init_db()


async def close_database() -> None:
    """Закрывает подключение к базе данных при завершении приложения."""
    await database.close()


# Пример использования
if __name__ == "__main__":
    async def main():
        # Инициализация
        await init_database()
        
        # Использование
        async with database.get_session() as session:
            result = await session.execute(text("SELECT version()"))
            version = await result.fetchone()
            print(f"PostgreSQL версия: {version[0]}")
        
        # Закрытие
        await close_database()
    
    asyncio.run(main())
