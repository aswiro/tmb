from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from database.models import CaptchaSetting

from keyboards.filters import FiltersCallbackFactory

from .base import KeyboardBuilder


class CaptchaCallbackFactory(CallbackData, prefix="captcha"):
    """Фабрика колбэков для действий с настройками каптчи"""

    action: str  # settings, update, back_to_filters
    group_id: int | None = None
    key: str | None = None
    value: bool | int | str | None = None


def get_captcha_settings_keyboard(captcha_settings: CaptchaSetting):
    """Создает клавиатуру с настройками каптчи для группы"""
    keyboard = KeyboardBuilder.inline()

    # Основные настройки каптчи
    settings_config = [
        {
            "key": "captcha_type",
            "name": _("captcha-type"),
            "type": "select",
            "options": ["standard", "math"],
        },
        {
            "key": "captcha_size",
            "name": _("captcha-size"),
            "type": "select",
            "options": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "labels": [
                ("256x144"),
                ("426x240"),
                ("640x360"),
                ("768x432"),
                ("800x450"),
                ("848x480"),
                ("960x540"),
                ("1024x576"),
                ("1152x648"),
                ("1280x720"),
                ("1366x768"),
                ("1600x900"),
                ("1920x1080"),
            ],
        },
        {
            "key": "difficulty_level",
            "name": _("captcha-difficulty"),
            "type": "select",
            "options": [0, 1, 2, 3, 4, 5],
            "labels": [
                _("easy"),
                _("light"),
                _("medium"),
                _("hard"),
                _("expert"),
                _("nightmare"),
            ],
        },
        {
            "key": "chars_mode",
            "name": _("captcha-chars-mode"),
            "type": "select",
            "options": [_("nums"), _("hex"), _("ascii")],
        },
        {
            "key": "multicolor",
            "name": _("captcha-multicolor"),
            "type": "bool",
        },
        {
            "key": "margin",
            "name": _("captcha-margin"),
            "type": "bool",
        },
        {
            "key": "allow_multiplication",
            "name": _("captcha-multiplication"),
            "type": "bool",
        },
        {
            "key": "timeout_seconds",
            "name": _("captcha-timeout"),
            "type": "number",
        },
        {
            "key": "max_attempts",
            "name": _("captcha-max-attempts"),
            "type": "number",
        },
        {
            "key": "auto_kick_on_fail",
            "name": _("captcha-auto-kick"),
            "type": "bool",
        },
    ]

    # Добавляем кнопки для каждой настройки
    for setting in settings_config:
        key = setting["key"]
        # Проверяем, нужно ли показывать кнопку allow_multiplication
        if key == "allow_multiplication" and captcha_settings.captcha_type != "math":
            continue
        name = setting["name"]
        setting_type = setting["type"]
        value = getattr(captcha_settings, key)

        if setting_type == "bool":
            emoji = "✅" if value else "❌"
            text = f"{emoji} {name}"
        elif setting_type == "select":
            if "labels" in setting:
                # Находим индекс текущего значения и берем соответствующий label
                try:
                    index = setting["options"].index(value)
                    display_value = setting["labels"][index]
                except (ValueError, IndexError):
                    display_value = str(value)
            else:
                display_value = str(value)
            text = f"⚙️ {name}: {display_value}"
        else:  # number или другие типы
            display_value = str(value)
            text = f"⚙️ {name}: {display_value}"

        keyboard.add_button(
            text=text,
            callback_data=CaptchaCallbackFactory(
                action="update",
                group_id=captcha_settings.group_id,
                key=key,
                value=value,
            ).pack(),
        )

    # Размещаем по 1 кнопке в ряд для лучшей читаемости
    keyboard.set_layout([1])

    # Добавляем кнопку "Предпросмотр"
    keyboard.add_button(
        text=_("preview-captcha"),
        callback_data=CaptchaCallbackFactory(
            action="preview",
            group_id=captcha_settings.group_id,
        ).pack(),
    )

    # Добавляем кнопку "Назад к фильтрам"
    keyboard.add_button(
        text=_("back-to-filters"),
        callback_data=FiltersCallbackFactory(
            action="filters", group_id=captcha_settings.group_id
        ).pack(),
    )

    return keyboard.build()


def get_captcha_type_keyboard(group_id: int, current_value: str):
    """Создает клавиатуру для выбора типа каптчи"""
    keyboard = KeyboardBuilder.inline()

    options = [
        {"value": "standard", "label": _("captcha-type-standard")},
        {"value": "math", "label": _("captcha-type-math")},
    ]

    for option in options:
        emoji = "✅" if option["value"] == current_value else "⚪"
        text = f"{emoji} {option['label']}"

        keyboard.add_button(
            text=text,
            callback_data=CaptchaCallbackFactory(
                action="set_value",
                group_id=group_id,
                key="captcha_type",
                value=option["value"],
            ).pack(),
        )

    # Кнопка назад
    keyboard.add_button(
        text=_("back"),
        callback_data=CaptchaCallbackFactory(
            action="settings", group_id=group_id
        ).pack(),
    )
    keyboard.set_layout([2, 1])

    return keyboard.build()


def get_captcha_size_keyboard(group_id: int, current_value: int):
    """Создает клавиатуру для выбора размера каптчи"""
    keyboard = KeyboardBuilder.inline()

    options = [
        {"value": 0, "label": "256x144"},
        {"value": 1, "label": "426x240"},
        {"value": 2, "label": "640x360"},
        {"value": 3, "label": "768x432"},
        {"value": 4, "label": "800x450"},
        {"value": 5, "label": "848x480"},
        {"value": 6, "label": "960x540"},
        {"value": 7, "label": "1024x576"},
        {"value": 8, "label": "1152x648"},
        {"value": 9, "label": "1280x720"},
        {"value": 10, "label": "1366x768"},
        {"value": 11, "label": "1600x900"},
        {"value": 12, "label": "1920x1080"},
    ]

    for option in options:
        emoji = "✅" if option["value"] == current_value else "⚪"
        text = f"{emoji} {option['label']}"

        keyboard.add_button(
            text=text,
            callback_data=CaptchaCallbackFactory(
                action="set_value",
                group_id=group_id,
                key="captcha_size",
                value=option["value"],
            ).pack(),
        )

    # Кнопка назад
    keyboard.add_button(
        text=_("back"),
        callback_data=CaptchaCallbackFactory(
            action="settings", group_id=group_id
        ).pack(),
    )
    keyboard.set_layout([3, 3, 3, 3, 1])
    return keyboard.build()


def get_captcha_difficulty_keyboard(group_id: int, current_value: int):
    """Создает клавиатуру для выбора сложности каптчи"""
    keyboard = KeyboardBuilder.inline()

    options = [
        {"value": 0, "label": _("easy")},
        {"value": 1, "label": _("light")},
        {"value": 2, "label": _("medium")},
        {"value": 3, "label": _("hard")},
        {"value": 4, "label": _("expert")},
        {"value": 5, "label": _("nightmare")},
    ]

    for option in options:
        emoji = "✅" if option["value"] == current_value else "⚪"
        text = f"{emoji} {option['label']}"

        keyboard.add_button(
            text=text,
            callback_data=CaptchaCallbackFactory(
                action="set_value",
                group_id=group_id,
                key="difficulty_level",
                value=option["value"],
            ).pack(),
        )

    # Кнопка назад
    keyboard.add_button(
        text=_("back"),
        callback_data=CaptchaCallbackFactory(
            action="settings", group_id=group_id
        ).pack(),
    )
    keyboard.set_layout([3, 3, 1])

    return keyboard.build()


def get_captcha_chars_mode_keyboard(group_id: int, current_value: int):
    """Создает клавиатуру для выбора режима символов каптчи"""
    keyboard = KeyboardBuilder.inline()

    options = [
        {"value": "nums", "label": _("nums")},
        {"value": "hex", "label": _("hex")},
        {"value": "ascii", "label": _("ascii")},
    ]

    for option in options:
        emoji = "✅" if option["value"] == current_value else "⚪"
        text = f"{emoji} {option['label']}"

        keyboard.add_button(
            text=text,
            callback_data=CaptchaCallbackFactory(
                action="set_value",
                group_id=group_id,
                key="chars_mode",
                value=option["value"],
            ).pack(),
        )

    # Кнопка назад
    keyboard.add_button(
        text=_("back"),
        callback_data=CaptchaCallbackFactory(
            action="settings", group_id=group_id
        ).pack(),
    )
    keyboard.set_layout([3, 1])

    return keyboard.build()


def get_back_to_captcha_settings_keyboard(group_id: int):
    """Создает клавиатуру с кнопкой "Назад" к настройкам капчи."""
    keyboard = KeyboardBuilder.inline()
    keyboard.add_button(
        text=_("back"),
        callback_data=CaptchaCallbackFactory(
            action="settings", group_id=group_id
        ).pack(),
    )
    return keyboard.build()
