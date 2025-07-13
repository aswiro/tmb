# config/__init__.py
"""Модуль конфигурации приложения.

Этот модуль содержит настройки и конфигурацию для всего приложения,
включая настройки базы данных, Redis, логирования и администраторов.
"""

from .settings import settings
from .admin_list import load_admin_ids
from .logger import setup_logger

__all__ = ["settings", "load_admin_ids", "setup_logger"]
