from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.i18n import gettext as _
from database.unit_of_work import UnitOfWork
from keyboards.captcha import (
    CaptchaCallbackFactory,
    get_back_to_captcha_settings_keyboard,
    get_captcha_chars_mode_keyboard,
    get_captcha_difficulty_keyboard,
    get_captcha_settings_keyboard,
    get_captcha_size_keyboard,
    get_captcha_type_keyboard,
)
from keyboards.filters import FiltersCallbackFactory
from utilites.captcha_generator import CaptchaGenerators


router = Router()


class CaptchaStates(StatesGroup):
    waiting_for_timeout = State()
    waiting_for_max_attempts = State()


@router.callback_query(FiltersCallbackFactory.filter(F.action == "captcha_settings"))
async def captcha_settings(
    callback: CallbackQuery, callback_data: FiltersCallbackFactory, uow: UnitOfWork
):
    """Показать настройки каптчи для группы"""
    group_id = callback_data.group_id

    async with uow:
        # Получаем настройки каптчи для группы
        captcha_settings = await uow.captcha_service.get_captcha_settings(group_id)

        if not captcha_settings:
            # Если настроек нет, создаем их с дефолтными значениями
            captcha_settings = (
                await uow.captcha_service.create_default_captcha_settings(
                    group_id=group_id
                )
            )
            await uow.commit()
        # for key, value in captcha_settings:
        #     logger.debug(f"Key: {key} - Value: {value}")
    # Создаем клавиатуру с настройками
    keyboard = get_captcha_settings_keyboard(captcha_settings)

    # Отправляем сообщение с настройками
    await callback.message.edit_text(
        text=_("captcha-settings-menu"),
        reply_markup=keyboard,
    )

    await callback.answer()


@router.callback_query(CaptchaCallbackFactory.filter(F.action == "update"))
async def captcha_update_setting(
    callback: CallbackQuery,
    callback_data: CaptchaCallbackFactory,
    uow: UnitOfWork,
    state: FSMContext,
):
    """Обработка обновления настройки каптчи"""
    group_id = callback_data.group_id
    key = callback_data.key
    current_value = callback_data.value

    # В зависимости от типа настройки показываем соответствующую клавиатуру
    if key in ["auto_kick_on_fail", "multicolor", "allow_multiplication", "margin"]:
        # Для булевых значений сразу переключаем
        current_value = int(current_value)
        new_value = bool(not current_value)

        async with uow:
            await uow.captcha_service.update_captcha_setting(
                group_id=group_id, setting_name=key, value=new_value
            )
            await uow.commit()

            # Получаем обновленные настройки
            captcha_settings = await uow.captcha_service.get_captcha_settings(group_id)
        # Обновляем клавиатуру
        keyboard = get_captcha_settings_keyboard(captcha_settings)

        await callback.message.edit_reply_markup(
            reply_markup=keyboard,
        )
        await callback.answer(_("setting-updated"))

    elif key == "captcha_type":
        # Показываем клавиатуру выбора типа каптчи
        keyboard = get_captcha_type_keyboard(group_id, current_value)

        await callback.message.edit_text(
            text=_("select-captcha-type"),
            reply_markup=keyboard,
        )
        await callback.answer()

    elif key == "captcha_size":
        # Показываем клавиатуру выбора размера каптчи
        keyboard = get_captcha_size_keyboard(group_id, current_value)

        await callback.message.edit_text(
            text=_("select-captcha-size"),
            reply_markup=keyboard,
        )
        await callback.answer()

    elif key == "difficulty_level":
        # Показываем клавиатуру выбора сложности каптчи
        keyboard = get_captcha_difficulty_keyboard(group_id, current_value)

        await callback.message.edit_text(
            text=_("select-captcha-difficulty"),
            reply_markup=keyboard,
        )
        await callback.answer()
    elif key == "chars_mode":
        # Показываем клавиатуру выбора режима символов каптчи
        keyboard = get_captcha_chars_mode_keyboard(group_id, current_value)

        await callback.message.edit_text(
            text=_("select-captcha-chars-mode"),
            reply_markup=keyboard,
        )
        await callback.answer()

    elif key == "timeout_seconds":
        await state.set_state(CaptchaStates.waiting_for_timeout)
        keyboard = get_back_to_captcha_settings_keyboard(group_id)
        await callback.message.edit_text(
            text=_("enter-new-value").format(
                setting=_(f"captcha-{key.replace('_', '-')}")
            ),
            reply_markup=keyboard,
        )
    elif key == "max_attempts":
        await state.set_state(CaptchaStates.waiting_for_max_attempts)
        keyboard = get_back_to_captcha_settings_keyboard(group_id)
        await callback.message.edit_text(
            text=_("enter-new-value").format(
                setting=_(f"captcha-{key.replace('_', '-')}")
            ),
            reply_markup=keyboard,
        )

    await state.update_data(group_id=group_id, message_id=callback.message.message_id)


@router.message(CaptchaStates.waiting_for_timeout)
@router.message(CaptchaStates.waiting_for_max_attempts)
async def process_numeric_setting_input(
    message: Message, state: FSMContext, uow: UnitOfWork
):
    """Обработка ввода нового числового значения для настройки капчи."""
    try:
        new_value = int(message.text)
    except (ValueError, TypeError):
        await message.answer(_("invalid-numeric-value"))
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    current_state = await state.get_state()

    if current_state == CaptchaStates.waiting_for_timeout.state:
        key = "timeout_seconds"
    elif current_state == CaptchaStates.waiting_for_max_attempts.state:
        key = "max_attempts"
    else:
        return  # Should not happen

    async with uow:
        await uow.captcha_service.update_captcha_setting(
            group_id=group_id, setting_name=key, value=new_value
        )
        await uow.commit()
        captcha_settings = await uow.captcha_service.get_captcha_settings(group_id)

    await state.clear()

    keyboard = get_captcha_settings_keyboard(captcha_settings)
    await message.answer(
        text=_("captcha-settings-menu"),
        reply_markup=keyboard,
    )
    # await message.answer(_("setting-updated"))


@router.callback_query(CaptchaCallbackFactory.filter(F.action == "set_value"))
async def captcha_set_value(
    callback: CallbackQuery, callback_data: CaptchaCallbackFactory, uow: UnitOfWork
):
    """Установка нового значения настройки каптчи"""
    group_id = callback_data.group_id
    key = callback_data.key
    new_value = callback_data.value

    # Преобразование типов для определенных ключей
    if key in [
        "captcha_size",
        "difficulty_level",
    ]:
        try:
            new_value = int(new_value)
        except (ValueError, TypeError):
            await callback.answer(_("invalid-numeric-value"), show_alert=True)
            return

    async with uow:
        # Обновляем настройку
        await uow.captcha_service.update_captcha_setting(
            group_id=group_id, setting_name=key, value=new_value
        )
        await uow.commit()

        # Получаем обновленные настройки
        captcha_settings = await uow.captcha_service.get_captcha_settings(group_id)

    # Возвращаемся к главному меню настроек каптчи
    keyboard = get_captcha_settings_keyboard(captcha_settings)

    await callback.message.edit_text(
        text=_("captcha-settings-menu"),
        reply_markup=keyboard,
    )

    await callback.answer(_("setting-updated"))


@router.callback_query(CaptchaCallbackFactory.filter(F.action == "preview"))
async def captcha_preview(
    callback: CallbackQuery,
    callback_data: CaptchaCallbackFactory,
    uow: UnitOfWork,
):
    """Просмотр текущей каптчи"""
    group_id = callback_data.group_id

    async with uow:
        captcha_settings = await uow.captcha_service.get_captcha_settings(group_id)
    generator = CaptchaGenerators(captcha_settings)
    captcha_photo_path = await generator.get_captcha()

    if not captcha_photo_path:
        await callback.answer(_("error-generating-captcha"), show_alert=True)
        return

    photo = FSInputFile(captcha_photo_path)
    keyboard = get_back_to_captcha_settings_keyboard(group_id)

    await callback.message.answer_photo(
        photo=photo,
        caption=_("captcha-preview-caption"),
        reply_markup=keyboard,
    )

    await callback.answer()


@router.callback_query(CaptchaCallbackFactory.filter(F.action == "settings"))
async def captcha_back_to_settings(
    callback: CallbackQuery, callback_data: CaptchaCallbackFactory, uow: UnitOfWork
):
    """Возврат к главному меню настроек каптчи"""
    group_id = callback_data.group_id

    async with uow:
        captcha_settings = await uow.captcha_service.get_captcha_settings(group_id)

    keyboard = get_captcha_settings_keyboard(captcha_settings)

    await callback.message.edit_text(
        text=_("captcha-settings-menu"),
        reply_markup=keyboard,
    )

    await callback.answer()
