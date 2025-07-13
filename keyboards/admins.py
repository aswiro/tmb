from keyboards.buttons import (
    get_ad_menu,
    get_admin_back_to_menu,
    get_change_language,
    get_filters_menu,
    get_my_groups,
)
from keyboards.language import get_language_keyboard

from .base import KeyboardBuilder


def get_admin_main_menu():
    """Создает главное меню администратора"""
    keyboard = KeyboardBuilder.inline()

    # Добавляем кнопки меню
    my_groups_btn = get_my_groups()
    keyboard.add_button(
        text=my_groups_btn.text, callback_data=my_groups_btn.callback_data
    )
    keyboard.add_row()

    filters_btn = get_filters_menu()
    keyboard.add_button(text=filters_btn.text, callback_data=filters_btn.callback_data)
    keyboard.add_row()

    ad_menu_btn = get_ad_menu()
    keyboard.add_button(text=ad_menu_btn.text, callback_data=ad_menu_btn.callback_data)

    language_btn = get_change_language()
    keyboard.add_button(
        text=language_btn.text, callback_data=language_btn.callback_data
    )
    keyboard.set_layout([1])

    return keyboard.build()


def get_admin_language_keyboard():
    """Создает клавиатуру для выбора языка для администратора"""
    return get_language_keyboard(get_admin_back_to_menu())
