"""Базовые классы для создания клавиатур."""

from abc import ABC, abstractmethod
from typing import Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class BaseKeyboardBuilder(ABC):
    """Базовый класс для создания клавиатур."""

    def __init__(self):
        self._buttons: list[dict[str, Any]] = []
        self._layout: list[int] | None = None

    @abstractmethod
    def build(self) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
        """Создать клавиатуру."""
        pass

    def add_button(
        self,
        text: str,
        callback_data: str | None = None,
        url: str | None = None,
        **kwargs,
    ) -> "BaseKeyboardBuilder":
        """Добавить кнопку."""
        button_data = {
            "text": text,
            "callback_data": callback_data,
            "url": url,
            **kwargs,
        }
        self._buttons.append(button_data)
        return self

    def add_button_object(
        self, button: InlineKeyboardButton | KeyboardButton
    ) -> "BaseKeyboardBuilder":
        """Добавить готовую кнопку."""
        if isinstance(button, InlineKeyboardButton):
            self._buttons.append(
                {
                    "text": button.text,
                    "callback_data": button.callback_data,
                    "url": button.url,
                }
            )
        elif isinstance(button, KeyboardButton):
            self._buttons.append(
                {
                    "text": button.text,
                    "request_contact": getattr(button, "request_contact", None),
                    "request_location": getattr(button, "request_location", None),
                }
            )
        return self

    def add_row(self) -> "BaseKeyboardBuilder":
        """Добавить новую строку (разделитель)."""
        self._buttons.append({"_row_separator": True})
        return self

    def set_layout(self, layout: list[int]) -> "BaseKeyboardBuilder":
        """Установить макет клавиатуры."""
        self._layout = layout
        return self

    def clear(self) -> "BaseKeyboardBuilder":
        """Очистить все кнопки."""
        self._buttons.clear()
        self._layout = None
        return self


class InlineKeyboardFactory(BaseKeyboardBuilder):
    """Фабрика для создания inline клавиатур."""

    def build(self) -> InlineKeyboardMarkup:
        """Создать inline клавиатуру."""
        builder = InlineKeyboardBuilder()

        for button_data in self._buttons:
            if button_data.get("_row_separator"):
                builder.row()
                continue

            button = InlineKeyboardButton(
                text=button_data["text"],
                callback_data=button_data.get("callback_data"),
                url=button_data.get("url"),
            )
            builder.add(button)

        if self._layout:
            builder.adjust(*self._layout)

        return builder.as_markup()


class ReplyKeyboardFactory(BaseKeyboardBuilder):
    """Фабрика для создания reply клавиатур."""

    def __init__(self, resize_keyboard: bool = True, one_time_keyboard: bool = False):
        super().__init__()
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard

    def build(self) -> ReplyKeyboardMarkup:
        """Создать reply клавиатуру."""
        builder = ReplyKeyboardBuilder()

        for button_data in self._buttons:
            if button_data.get("_row_separator"):
                builder.row()
                continue

            button = KeyboardButton(
                text=button_data["text"],
                request_contact=button_data.get("request_contact", False),
                request_location=button_data.get("request_location", False),
            )
            builder.add(button)

        if self._layout:
            builder.adjust(*self._layout)

        return builder.as_markup(
            resize_keyboard=self.resize_keyboard,
            one_time_keyboard=self.one_time_keyboard,
        )


class KeyboardBuilder:
    """Удобный интерфейс для создания клавиатур."""

    @staticmethod
    def inline() -> InlineKeyboardFactory:
        """Создать inline клавиатуру."""
        return InlineKeyboardFactory()

    @staticmethod
    def reply(
        resize_keyboard: bool = True, one_time_keyboard: bool = False
    ) -> ReplyKeyboardFactory:
        """Создать reply клавиатуру."""
        return ReplyKeyboardFactory(resize_keyboard, one_time_keyboard)


# Миксин для добавления общих методов в существующие классы
class KeyboardMixin:
    """Миксин с общими методами для клавиатур."""

    @staticmethod
    def create_back_button(text: str, callback_data: str) -> InlineKeyboardButton:
        """Создать кнопку возврата."""
        return InlineKeyboardButton(text=text, callback_data=callback_data)

    @staticmethod
    def create_url_button(text: str, url: str) -> InlineKeyboardButton:
        """Создать кнопку с URL."""
        return InlineKeyboardButton(text=text, url=url)

    @staticmethod
    def create_callback_button(text: str, callback_data: str) -> InlineKeyboardButton:
        """Создать кнопку с callback_data."""
        return InlineKeyboardButton(text=text, callback_data=callback_data)
