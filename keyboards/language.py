from aiogram.types import InlineKeyboardButton
from config import LOCALES_DIR

from .base import KeyboardBuilder


# Словарь соответствия кодов языков и их отображения
language_display = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español",
    "it": "🇮🇹 Italiano",
    "pt": "🇵🇹 Português",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "ar": "🇸🇦 العربية",
    "hi": "🇮🇳 हिन्दी",
    "tr": "🇹🇷 Türkçe",
    "pl": "🇵🇱 Polski",
    "nl": "🇳🇱 Nederlands",
    "sv": "🇸🇪 Svenska",
    "da": "🇩🇰 Dansk",
    "no": "🇳🇴 Norsk",
    "fi": "🇫🇮 Suomi",
    "cs": "🇨🇿 Čeština",
    "sk": "🇸🇰 Slovenčina",
    "hu": "🇭🇺 Magyar",
    "ro": "🇷🇴 Română",
    "bg": "🇧🇬 Български",
    "hr": "🇭🇷 Hrvatski",
    "sr": "🇷🇸 Српски",
    "sl": "🇸🇮 Slovenščina",
    "et": "🇪🇪 Eesti",
    "lv": "🇱🇻 Latviešu",
    "lt": "🇱🇹 Lietuvių",
    "uk": "🇺🇦 Українська",
    "be": "🇧🇾 Беларуская",
}


def language_list() -> list[str]:
    # Сканируем доступные языки
    available_languages = []
    if LOCALES_DIR.exists():
        for item in LOCALES_DIR.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                # Проверяем, что в папке есть LC_MESSAGES
                lc_messages_path = item / "LC_MESSAGES"
                if lc_messages_path.exists():
                    available_languages.append(item.name)

    # Сортируем языки для консистентности
    available_languages.sort()
    return available_languages


def get_language_keyboard(back_button: InlineKeyboardButton):
    """Создает клавиатуру для выбора языка на основе доступных локалей

    Args:
        back_button: Кнопка возврата (админская или пользовательская)
    """
    keyboard = KeyboardBuilder.inline()

    available_languages = language_list()

    # Создаем кнопки для доступных языков
    for lang_code in available_languages:
        display_name = language_display.get(lang_code, f"🌐 {lang_code.upper()}")
        keyboard.add_button(text=display_name, callback_data=f"lang:{lang_code}")

    # Добавляем кнопку возврата
    keyboard.add_button(text=back_button.text, callback_data=back_button.callback_data)

    # Выстраиваем кнопки в столбец
    keyboard.set_layout([1])

    return keyboard.build()
