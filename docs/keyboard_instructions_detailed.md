 # Руководство по созданию клавиатур в Telegram боте

Это руководство описывает архитектуру и принципы создания и управления клавиатурами в проекте.

## 1. Обзор архитектуры

Система клавиатур построена на базе `aiogram.utils.keyboard` с использованием кастомных фабрик и билдеров для упрощения процесса. Основная цель — предоставить гибкий и переиспользуемый интерфейс для создания как `inline`, так и `reply` клавиатур.

**Ключевые компоненты:**

-   `BaseKeyboardBuilder`: Абстрактный базовый класс, определяющий общий интерфейс для всех билдеров.
-   `InlineKeyboardFactory` и `ReplyKeyboardFactory`: Конкретные реализации для создания `inline` и `reply` клавиатур.
-   `KeyboardBuilder`: Фасад, предоставляющий статические методы `inline()` и `reply()` для удобного создания нужного типа клавиатуры.
-   `KeyboardMixin`: Миксин с хелперами для создания стандартных кнопок (URL, callback).
-   Модули-конструкторы (`admins.py`, `group.py`, `user.py`): Содержат функции, которые собирают конкретные клавиатуры для разных разделов бота.
-   `buttons.py`: Централизованное место для создания и хранения "атомарных" кнопок, которые переиспользуются в разных клавиатурах.

## 2. Структура файлов

-   `keyboards/base.py`: Ядро системы. Содержит базовые классы `BaseKeyboardBuilder`, `InlineKeyboardFactory`, `ReplyKeyboardFactory` и фасад `KeyboardBuilder`.
-   `keyboards/buttons.py`: Определяет функции для создания часто используемых кнопок (например, "Назад", "Сменить язык"). Это помогает избежать дублирования кода и обеспечивает консистентность.
-   `keyboards/admins.py`: Клавиатуры, специфичные для администраторов (главное меню, меню языков).
-   `keyboards/group.py`: Клавиатуры для управления группами (список групп, добавление/удаление).
-   `keyboards/user.py`: Клавиатуры для обычных пользователей.
-   `keyboards/language.py`: Общая клавиатура для выбора языка, которая используется как для админов, так и для пользователей, принимая разную кнопку "Назад".

## 3. Принципы создания клавиатур

### 3.1. Базовое создание клавиатуры

Всегда начинайте с вызова `KeyboardBuilder`.

```python
# keyboards/admins.py

from .base import KeyboardBuilder

def get_admin_main_menu():
    """Создает главное меню администратора"""
    # 1. Создаем экземпляр inline клавиатуры
    keyboard = KeyboardBuilder.inline()

    # 2. Добавляем кнопки
    keyboard.add_button(text="Мои группы", callback_data="my_groups")
    keyboard.add_row() # Переход на новую строку
    keyboard.add_button(text="Фильтры", callback_data="filters_menu")
    keyboard.add_row()
    keyboard.add_button(text="Сменить язык", callback_data="change_language")

    # 3. Собираем и возвращаем клавиатуру
    return keyboard.build()
```

### 3.2. Управление расположением (`set_layout`)

Метод `set_layout` позволяет гибко управлять количеством кнопок в ряду. Он принимает список целых чисел, где каждое число — это количество кнопок в соответствующем ряду.

**Пример: 2 кнопки в первом ряду, 1 во втором.**

```python
# keyboards/user.py

def get_user_main_menu():
    keyboard = KeyboardBuilder.inline()

    # Добавляем 3 кнопки подряд
    keyboard.add_button(text="Кнопка 1", callback_data="b1")
    keyboard.add_button(text="Кнопка 2", callback_data="b2")
    keyboard.add_button(text="Кнопка 3", callback_data="b3")

    # Устанавливаем макет: [2, 1]
    # Результат:
    # [ Кнопка 1 ] [ Кнопка 2 ]
    # [      Кнопка 3      ]
    keyboard.set_layout([2, 1])

    return keyboard.build()
```

### 3.3. Динамическое создание кнопок из списков

Часто нужно создавать кнопки на основе данных из базы данных (например, список групп).

```python
# keyboards/group.py

def get_groups_list_keyboard(groups: list[Group]):
    keyboard = KeyboardBuilder.inline()

    # Создаем кнопки в цикле
    for group in groups:
        keyboard.add_button(
            text=f"{group.title}",
            callback_data=f"remove_group:{group.id}"
        )

    # Можно также динамически настроить layout
    layout = [2 if len(g.title) < 15 else 1 for g in groups]
    keyboard.set_layout(layout)

    # Добавляем служебные кнопки
    keyboard.add_button_object(get_admin_back_to_menu())

    return keyboard.build()
```

### 3.4. Использование готовых кнопок (`add_button_object`)

Чтобы не дублировать создание одних и тех же кнопок, они вынесены в `keyboards/buttons.py`. Метод `add_button_object` принимает готовый объект `InlineKeyboardButton`.

```python
# keyboards/buttons.py

from aiogram.types import InlineKeyboardButton

def get_admin_back_to_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="admin_menu")

# keyboards/group.py
from .buttons import get_admin_back_to_menu

def get_group_management_keyboard():
    keyboard = KeyboardBuilder.inline()
    # ...
    keyboard.add_button_object(get_admin_back_to_menu())
    return keyboard.build()
```

### 3.5. Размещение служебных кнопок

Служебные кнопки (например, "Назад", "Добавить") обычно размещаются внизу клавиатуры.

**Две кнопки в ряд:**

```python
# Добавляем кнопки в конце
keyboard.add_button_object(get_add_group())
keyboard.add_button_object(get_admin_back_to_menu())

# Получаем текущее количество кнопок
num_buttons = len(keyboard._buttons)

# Если до этого были кнопки, нужно учесть их в layout
# Предположим, у нас уже есть layout для списка групп
existing_layout = [1, 2, 1]
# Добавляем ряд с двумя кнопками
final_layout = existing_layout + [2]
keyboard.set_layout(final_layout)
```

Если `set_layout` не используется, можно просто добавить кнопки, и они встанут в ряд по одной, если не использовать `add_row()`.

## 4. Рекомендации

1.  **Переиспользуйте кнопки**: Всегда выносите часто используемые кнопки в `keyboards/buttons.py`.
2.  **Используйте `set_layout`**: Для нетривиальных расположений `set_layout` является предпочтительным способом.
3.  **Инкапсулируйте логику**: Каждая функция в `keyboards/*.py` должна отвечать за создание одной конкретной клавиатуры.
4.  **Используйте `CallbackData`**: Для сложных `callback_data` используйте фабрики колбэков `aiogram` для большей структурированности.
