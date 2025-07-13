from keyboards.buttons import (
    get_change_language,
    get_user_back_to_menu,
)
from keyboards.language import get_language_keyboard

from .base import KeyboardBuilder


def get_user_main_menu():
    """Создает главное меню пользователя"""
    keyboard = KeyboardBuilder.inline()

    # Добавляем кнопку смены языка
    language_btn = get_change_language()
    keyboard.add_button(
        text=language_btn.text, callback_data=language_btn.callback_data
    )

    # Настраиваем расположение: 2 кнопки в первом ряду, 1 во втором
    keyboard.set_layout([2, 1])

    return keyboard.build()


def get_user_language_keyboard():
    """Создает клавиатуру для выбора языка для пользователя"""
    return get_language_keyboard(get_user_back_to_menu())
