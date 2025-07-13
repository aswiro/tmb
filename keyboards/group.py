from database.models import Group

from keyboards.buttons import (
    GroupCallbackFactory,
    get_add_group,
    get_admin_back_to_menu,
)

from .base import KeyboardBuilder


def get_group_management_keyboard():
    """Создает клавиатуру для управления группами"""
    keyboard = KeyboardBuilder.inline()

    keyboard.add_button_object(get_add_group())
    keyboard.add_row()
    keyboard.add_button_object(get_admin_back_to_menu())

    return keyboard.build()


def get_groups_list_keyboard(groups: list[Group]):
    """Создает клавиатуру со списком групп для удаления"""
    keyboard = KeyboardBuilder.inline()

    # Добавляем кнопки групп
    for group in groups:
        keyboard.add_button(
            text=f"{group.title}",
            callback_data=GroupCallbackFactory(
                action="remove", group_id=group.id
            ).pack(),
        )

    # Определяем размещение кнопок в зависимости от длины текста
    # Если текст короткий (до 20 символов) - 2 кнопки в ряд, иначе - 1
    layout = []
    for group in groups:
        if len(group.title) <= 15:
            layout.append(2)  # 2 кнопки в ряд для коротких названий
        else:
            layout.append(1)  # 1 кнопка в ряд для длинных названий

    # Применяем динамическое размещение
    if layout:
        keyboard.set_layout(layout)

    # Добавляем кнопки управления в конце
    keyboard.add_button_object(get_add_group())
    keyboard.add_button_object(get_admin_back_to_menu())

    return keyboard.build()
