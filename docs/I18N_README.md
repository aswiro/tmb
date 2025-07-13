# Интернационализация (i18n) для TMB Bot

## Структура файлов

```
locales/
├── messages.pot          # Шаблон переводов (генерируется автоматически)
├── en/
│   └── LC_MESSAGES/
│       ├── messages.po   # Переводы на английский
│       ├── messages.mo   # Скомпилированные переводы
│       └── messages.ftl  # Fluent переводы
└── ru/
    └── LC_MESSAGES/
        ├── messages.po   # Переводы на русский
        ├── messages.mo   # Скомпилированные переводы
        └── messages.ftl  # Fluent переводы
```

## Команды для работы с переводами

### 1. Извлечение строк для перевода
```bash
pybabel extract -F babel.cfg -k _ -o locales/messages.pot .
```

### 2. Создание нового языка
```bash
pybabel init -i locales/messages.pot -d locales -l <язык>
```
Пример: `pybabel init -i locales/messages.pot -d locales -l de` (для немецкого)

### 3. Обновление существующих переводов
```bash
pybabel update -i locales/messages.pot -d locales
```

### 4. Компиляция переводов
```bash
pybabel compile -d locales
```

## Использование в коде

### В обработчиках
```python
from aiogram.utils.i18n import gettext as _

# Простой перевод
message = _("hello")

# С параметрами (используйте format)
message = _("user-greeting").format(name=user.name)
```

### В клавиатурах
```python
from aiogram.utils.i18n import gettext as _

button = InlineKeyboardButton(
    text=_("add-group"),
    callback_data="add_group"
)
```

## Добавление нового языка

1. Создайте новый язык:
   ```bash
   pybabel init -i locales/messages.pot -d locales -l <код_языка>
   ```

2. Переведите строки в файле `locales/<код_языка>/LC_MESSAGES/messages.po`

3. Скомпилируйте переводы:
   ```bash
   pybabel compile -d locales
   ```

4. Добавьте язык в список доступных языков в коде бота

## Поддерживаемые языки

- 🇷🇺 Русский (ru) - основной язык
- 🇺🇸 Английский (en)

## Примечания

- Файлы `.mo` генерируются автоматически и не должны редактироваться вручную
- Файлы `.po` содержат переводы и редактируются вручную
- Файл `.pot` - это шаблон, генерируется из исходного кода
- Используйте эмодзи в переводах для лучшего UX
- Всегда компилируйте переводы после изменений