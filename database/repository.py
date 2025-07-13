# repository.py - базовый репозиторий для работы с данными
"""Базовый репозиторий для работы с данными.

Этот модуль содержит базовый класс Repository, который предоставляет
стандартные методы для работы с данными (CRUD операции).
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Типы для Generic репозитория
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый репозиторий для работы с моделями.
    
    Предоставляет стандартные CRUD операции:
    - create: создание записи
    - get: получение записи по ID
    - get_multi: получение нескольких записей
    - update: обновление записи
    - delete: удаление записи
    
    Args:
        model: Класс модели SQLAlchemy
        session: Сессия базы данных
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Создает новую запись в базе данных.
        
        Args:
            obj_in: Данные для создания записи
            
        Returns:
            Созданная запись
        """
        try:
            # Если obj_in это Pydantic модель, конвертируем в dict
            if hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump()
            elif hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict()
            else:
                obj_data = obj_in
            
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            logger.debug(f"Создана запись {self.model.__name__} с ID: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при создании {self.model.__name__}: {e}")
            raise
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """Получает запись по ID.
        
        Args:
            id: Идентификатор записи
            
        Returns:
            Найденная запись или None
        """
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Ошибка при получении {self.model.__name__} с ID {id}: {e}")
            raise
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Получает несколько записей с пагинацией и фильтрацией.
        
        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            **filters: Дополнительные фильтры
            
        Returns:
            Список найденных записей
        """
        try:
            stmt = select(self.model)
            
            # Применяем фильтры
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    stmt = stmt.where(getattr(self.model, field) == value)
            
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка {self.model.__name__}: {e}")
            raise
    
    async def update(
        self, 
        id: Any, 
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Обновляет запись по ID.
        
        Args:
            id: Идентификатор записи
            obj_in: Данные для обновления
            
        Returns:
            Обновленная запись или None если не найдена
        """
        try:
            # Получаем существующую запись
            db_obj = await self.get(id)
            if not db_obj:
                return None
            
            # Подготавливаем данные для обновления
            if hasattr(obj_in, 'model_dump'):
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Обновляем поля
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            logger.debug(f"Обновлена запись {self.model.__name__} с ID: {id}")
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при обновлении {self.model.__name__} с ID {id}: {e}")
            raise
    
    async def delete(self, id: Any) -> bool:
        """Удаляет запись по ID.
        
        Args:
            id: Идентификатор записи
            
        Returns:
            True если запись была удалена, False если не найдена
        """
        try:
            # Проверяем существование записи
            db_obj = await self.get(id)
            if not db_obj:
                return False
            
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.debug(f"Удалена запись {self.model.__name__} с ID: {id}")
                return True
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при удалении {self.model.__name__} с ID {id}: {e}")
            raise
    
    async def count(self, **filters) -> int:
        """Подсчитывает количество записей с фильтрацией.
        
        Args:
            **filters: Фильтры для подсчета
            
        Returns:
            Количество записей
        """
        try:
            from sqlalchemy import func
            
            stmt = select(func.count(self.model.id))
            
            # Применяем фильтры
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    stmt = stmt.where(getattr(self.model, field) == value)
            
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Ошибка при подсчете {self.model.__name__}: {e}")
            raise
    
    async def exists(self, id: Any) -> bool:
        """Проверяет существование записи по ID.
        
        Args:
            id: Идентификатор записи
            
        Returns:
            True если запись существует
        """
        try:
            from sqlalchemy import exists as sql_exists
            
            stmt = select(sql_exists().where(self.model.id == id))
            result = await self.session.execute(stmt)
            return result.scalar() or False
            
        except Exception as e:
            logger.error(f"Ошибка при проверке существования {self.model.__name__} с ID {id}: {e}")
            raise
    
    async def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Создает несколько записей за один раз.
        
        Args:
            objects: Список данных для создания записей
            
        Returns:
            Список созданных записей
        """
        try:
            db_objects = []
            for obj_in in objects:
                if hasattr(obj_in, 'model_dump'):
                    obj_data = obj_in.model_dump()
                elif hasattr(obj_in, 'dict'):
                    obj_data = obj_in.dict()
                else:
                    obj_data = obj_in
                
                db_obj = self.model(**obj_data)
                db_objects.append(db_obj)
            
            self.session.add_all(db_objects)
            await self.session.commit()
            
            # Обновляем объекты
            for db_obj in db_objects:
                await self.session.refresh(db_obj)
            
            logger.debug(f"Создано {len(db_objects)} записей {self.model.__name__}")
            return db_objects
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при массовом создании {self.model.__name__}: {e}")
            raise
