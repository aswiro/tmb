# app/config/__init__.py
from pathlib import Path

from .settings import Settings, settings


# Корневая директория проекта
BASE_DIR = Path(__file__).parent.parent

# # Директории
LOGS_DIR = BASE_DIR / "logs"
# MIGRATIONS_DIR = BASE_DIR / "orm" / "migrations"
LOCALES_DIR = BASE_DIR / "locales"

# # Создаем директории, если они не существуют
LOGS_DIR.mkdir(exist_ok=True)
# MIGRATIONS_DIR.mkdir(exist_ok=True)
LOCALES_DIR.mkdir(exist_ok=True)

# Настройки по умолчанию
DEFAULT_FILTERS = {
    "hashtag": "false",
    "url": "false",
    "email": "false",
    "ads": "false",
    "phone_number": "false",
    "forbidden_words": "false",
    "track_members": "false",
    "max_message_length": "50",
    "bonuses_enabled": "false",
    "bonus_per_user": "10",
    "bonus_checkpoint": "1000",
    "captcha": "false",
}

DEFAULT_CAPTCHA_SETTINGS = {
    "captcha_size_number": "2",
    "difficult_level": "1",
    "chars_mode": "nums",
    "multicolor": "False",
    "allow_multiplication": "False",
    "margin": "False",
    "captcha_type": "default",
}

# Константы для форматов
CONSOLE_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{file}:{line}</cyan> - <level>{message}</level>"
FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file}:{line} - {message}"

__all__ = [
    "LOGS_DIR",
    "LOCALES_DIR",
    "DEFAULT_FILTERS",
    "DEFAULT_CAPTCHA_SETTINGS",
    "CONSOLE_FORMAT",
    "FILE_FORMAT",
    "settings",
]
