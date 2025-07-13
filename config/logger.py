import sys

from loguru import logger

from config import CONSOLE_FORMAT, FILE_FORMAT, LOGS_DIR


# Создаем файл для логов
log_file = LOGS_DIR / "bot.log"


def setup_logger(level: str = "INFO") -> None:
    """Настройка логгера с указанным уровнем."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=level,
        colorize=True,
        serialize=True,
    )
    logger.add(
        log_file,
        format=FILE_FORMAT,
        level=level,
        rotation="1 day",
        retention="3 days",
        compression="zip",
        encoding="utf-8",
        serialize=True,
    )


def set_log_level(level: str) -> None:
    """Установка уровня логирования."""
    setup_logger(level)
