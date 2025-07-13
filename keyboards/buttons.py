from aiogram.filters.callback_data import CallbackData
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.i18n import gettext as _


class UserCallbackFactory(CallbackData, prefix="user"):
    """Фабрика колбэков для пользовательских действий"""

    action: str


class GroupCallbackFactory(CallbackData, prefix="group"):
    """Фабрика колбэков для действий с группами"""

    action: str  # add, list, remove_select, remove, back_to_menu
    group_id: int | None = None


class AdminCallbackFactory(CallbackData, prefix="admin"):
    """Фабрика колбэков для админских действий"""

    action: str


class AdCallbackFactory(CallbackData, prefix="ad"):
    action: str
    role: str = "advertiser"  # "advertiser" или "admin"
    item_id: int | None = None


# Функции для создания кнопок (вызываются после инициализации I18n)
def get_user_back_to_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("back-to-menu"),
        callback_data=UserCallbackFactory(action="back_to_menu").pack(),
    )


def get_change_language() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("change-language"),
        callback_data=UserCallbackFactory(action="change_language").pack(),
    )


def get_ad_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("ad-menu"),
        callback_data=AdCallbackFactory(action="ad_menu", role="advertiser").pack(),
    )


def get_admin_ad_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("admin-ad-menu"),
        callback_data=AdCallbackFactory(action="ad_menu", role="admin").pack(),
    )


def get_add_group() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("add-group"),
        callback_data=GroupCallbackFactory(action="add").pack(),
    )


def get_group_back_to_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("back-to-menu"),
        callback_data=GroupCallbackFactory(action="back_to_menu").pack(),
    )


def get_my_groups() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("my-groups"),
        callback_data=GroupCallbackFactory(action="list", group_id=None).pack(),
    )


def get_admin_back_to_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("back-to-menu"),
        callback_data=AdminCallbackFactory(action="back_to_menu").pack(),
    )


def get_filters_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=_("filters-menu"),
        callback_data=AdminCallbackFactory(action="filters_menu").pack(),
    )


def return_to_main_menu(user_role: str):
    """
    Возвращает кнопку возврата в главное меню в зависимости от роли пользователя.
    Используется для простых случаев, когда нужна только кнопка.

    Args:
        user_role: Роль пользователя ("admin" или "user")

    Returns:
        InlineKeyboardButton: Кнопка возврата в главное меню
    """
    if user_role == "admin":
        return get_admin_back_to_menu()
    return get_user_back_to_menu()


def get_main_menu_keyboard(user_role: str):
    """
    Возвращает полную клавиатуру главного меню в зависимости от роли пользователя.
    Используется, когда нужно вернуть пользователя в главное меню с полным набором кнопок.

    Args:
        user_role: Роль пользователя ("admin" или "user")

    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    # Импортируем здесь, чтобы избежать циклических импортов
    from keyboards.admins import get_admin_main_menu
    from keyboards.user import get_user_main_menu

    if user_role == "admin":
        return get_admin_main_menu()
    return get_user_main_menu()
