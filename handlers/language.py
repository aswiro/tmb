from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from config.settings import Settings
from database.unit_of_work import UnitOfWork
from keyboards.buttons import (
    AdminCallbackFactory,
    UserCallbackFactory,
    get_main_menu_keyboard,
)
from keyboards.user import get_user_language_keyboard
from loguru import logger


router = Router()


@router.callback_query(UserCallbackFactory.filter(F.action == "change_language"))
async def on_change_language_callback(callback: CallbackQuery):
    """Обработчик нажатия на кнопку 'Изменить язык' для пользователей"""
    await callback.answer()
    logger.debug("Start language change handler for user")
    await callback.message.edit_text(
        _("choose-language"),
        reply_markup=get_user_language_keyboard(),
    )


@router.callback_query(AdminCallbackFactory.filter(F.action == "change_language"))
async def on_admin_change_language_callback(callback: CallbackQuery):
    """Обработчик нажатия на кнопку 'Изменить язык' для админов"""
    await callback.answer()
    from keyboards.admins import get_admin_language_keyboard

    await callback.message.edit_text(
        _("choose-language"),
        reply_markup=get_admin_language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def on_language_select(
    callback: CallbackQuery, uow: UnitOfWork, i18n, settings: Settings
):
    """Обработчик выбора языка"""
    logger.debug("Continued language change handler")
    await callback.answer()

    # Извлекаем код языка из callback_data
    locale = callback.data.split(":")[1]

    # Сохраняем выбранный язык в базе данных
    user_id = callback.from_user.id
    async with uow:
        await uow.user_service.update_user(user_id, {"language_code": locale})

    # Обновляем текущий язык в I18n
    i18n.current_locale = locale
    if callback.from_user.id in settings.bot_admin_ids:
        keyboard = get_main_menu_keyboard(user_role="admin")
    else:
        keyboard = get_main_menu_keyboard(user_role="user")

    await callback.message.edit_text(_("language-changed"), reply_markup=keyboard)
