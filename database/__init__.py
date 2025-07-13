# database/__init__.py
"""Модуль для работы с базой данных.

Этот модуль содержит все компоненты для работы с базой данных:
- Модели данных
- Репозитории для доступа к данным
- Сервисы для бизнес-логики
- Утилиты для управления базой данных
"""

from .db_main import database
from .repository import BaseRepository
from .unit_of_work import UnitOfWork

__all__ = ["database", "BaseRepository", "UnitOfWork"]
