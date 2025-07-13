# logger.py - настройка логирования
"""Модуль для настройки системы логирования.

Этот модуль настраивает loguru для логирования событий приложения
с различными уровнями детализации и форматами вывода.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    compression: str = "zip",
    format_string: Optional[str] = None,
) -> None:
    """Настраивает систему логирования с помощью loguru.
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов (если None, логи только в консоль)
        rotation: Условие ротации логов (размер или время)
        retention: Время хранения старых логов
        compression: Тип сжатия архивных логов
        format_string: Пользовательский формат логов
    """
    # Удаляем стандартный обработчик loguru
    logger.remove()
    
    # Формат по умолчанию
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Добавляем обработчик для консоли
    logger.add(
        sys.stdout,
        format=format_string,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Добавляем обработчик для файла, если указан
    if log_file:
        # Создаем директорию для логов, если она не существует
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=format_string,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
        )
        
        logger.info(f"Логирование настроено. Файл логов: {log_file}")
    else:
        logger.info("Логирование настроено только для консоли")


def setup_bot_logger() -> None:
    """Настраивает логирование специально для Telegram бота.
    
    Использует предустановленные настройки, оптимальные для бота:
    - Уровень INFO
    - Ротация по размеру 10MB
    - Хранение логов 1 неделю
    - Сжатие в zip
    """
    # Создаем директорию для логов
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Настраиваем логирование
    setup_logger(
        log_level="INFO",
        log_file="logs/bot.log",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
    )
    
    # Добавляем отдельный файл для ошибок
    logger.add(
        "logs/errors.log",
        level="ERROR",
        rotation="5 MB",
        retention="2 weeks",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=True,
        encoding="utf-8",
    )
    
    logger.info("Логирование для бота настроено")


def get_logger(name: str):
    """Возвращает именованный логгер.
    
    Args:
        name: Имя логгера (обычно __name__ модуля)
        
    Returns:
        Настроенный логгер
    """
    return logger.bind(name=name)
