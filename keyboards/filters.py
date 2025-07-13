from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from database.models import FilterRule, Group

from keyboards.buttons import (
    AdminCallbackFactory,
    get_admin_back_to_menu,
)

from .base import KeyboardBuilder


class FiltersCallbackFactory(CallbackData, prefix="filters"):
    """Фабрика колбэков для действий с фильтрами"""

    action: str  # filters, update, back_to_menu
    group_id: int | None = None
    key: str | None = None
    value: bool | int | None = None


def get_groups_list_for_filters(groups: list[Group]):
    """Создает клавиатуру со списком групп для меню фильтров"""
    keyboard = KeyboardBuilder.inline()

    # Добавляем кнопки групп
    for group in groups:
        keyboard.add_button(
            text=f"{group.title}",
            callback_data=FiltersCallbackFactory(
                action="filters", group_id=group.id
            ).pack(),
        )

    keyboard.set_layout([1])

    # Добавляем кнопку возврата
    back_btn = get_admin_back_to_menu()
    keyboard.add_button(text=back_btn.text, callback_data=back_btn.callback_data)

    return keyboard.build()


def get_filters_list_for_group(filters: FilterRule):
    """Создает клавиатуру со списком фильтров для группы"""
    keyboard = KeyboardBuilder.inline()

    # Словарь с названиями фильтров и их переводами
    filter_names = {
        "hashtag": _("filter-hashtag"),
        "url": _("filter-url"),
        "email": _("filter-email"),
        "ads": _("filter-ads"),
        "phone_number": _("filter-phone-number"),
        "forbidden_words": _("filter-forbidden-words"),
        "track_members": _("filter-track-members"),
        "captcha": _("filter-captcha"),
        "max_message_length": _("filter-max-message-length"),
    }

    # Добавляем кнопки для базовых фильтров
    for field_name, display_name in filter_names.items():
        if hasattr(filters, field_name):
            value = getattr(filters, field_name)
            # Добавляем эмодзи в зависимости от значения
            if isinstance(value, bool):
                emoji = "✅" if value else "❌"
                text = f"{emoji} {display_name}"
            else:
                text = f"⚙️ {display_name}: {value}"

            keyboard.add_button(
                text=text,
                callback_data=FiltersCallbackFactory(
                    action="update", group_id=filters.id, key=field_name, value=value
                ).pack(),
            )

    # Условное добавление кнопки "Настройка каптчи" только если captcha включена
    if hasattr(filters, "captcha") and filters.captcha:
        keyboard.add_button(
            text=_("captcha-settings"),
            callback_data=FiltersCallbackFactory(
                action="captcha_settings", group_id=filters.id
            ).pack(),
        )

    # Условное добавление кнопки bonuses_enabled только если track_members включен
    if hasattr(filters, "track_members") and filters.track_members:
        field_name = "bonuses_enabled"
        display_name = _("filter-bonuses-enabled")
        value = getattr(filters, field_name)
        emoji = "✅" if value else "❌"
        text = f"{emoji} {display_name}"

        keyboard.add_button(
            text=text,
            callback_data=FiltersCallbackFactory(
                action="update", group_id=filters.id, key=field_name, value=value
            ).pack(),
        )

        # Условное добавление кнопок bonus_per_user и bonus_checkpoint только если bonuses_enabled включен
        if value:  # Если bonuses_enabled == True
            for field_name in ["bonus_per_user", "bonus_checkpoint"]:
                display_name = _(f"filter-{field_name.replace('_', '-')}")
                value = getattr(filters, field_name)
                text = f"⚙️ {display_name}: {value}"

                keyboard.add_button(
                    text=text,
                    callback_data=FiltersCallbackFactory(
                        action="update",
                        group_id=filters.id,
                        key=field_name,
                        value=value,
                    ).pack(),
                )

    # Размещаем по 1 кнопке в ряд для лучшей читаемости
    keyboard.set_layout([1])

    # Добавляем кнопку "Назад"
    keyboard.add_button(
        text=_("back-to-groups"),
        callback_data=AdminCallbackFactory(action="filters_menu").pack(),
    )

    return keyboard.build()


def get_back_to_filter_menu(group_id: int):
    """Создает клавиатуру для изменения значения фильтра"""
    keyboard = KeyboardBuilder.inline()

    # Добавляем кнопку "Назад"
    keyboard.add_button(
        text=_("back"),
        callback_data=FiltersCallbackFactory(
            action="filters", group_id=group_id
        ).pack(),
    )

    return keyboard.build()
