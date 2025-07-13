from aiogram import F, Router
from aiogram.filters.command import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from filters.admins import AdminFilter
from keyboards.buttons import (
    AdminCallbackFactory,
    get_main_menu_keyboard,
)


router = Router()

router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(CommandStart())
@router.callback_query(AdminCallbackFactory.filter(F.action == "back_to_menu"))
async def cmd_start_admin(update: Message | CallbackQuery):
    """Обработчик команды /start для администраторов"""
    if isinstance(update, Message):
        await update.answer(
            _("admin-welcome-message"),
            reply_markup=get_main_menu_keyboard(user_role="admin"),
        )
    elif isinstance(update, CallbackQuery):
        await update.answer()
        await update.message.edit_text(
            _("admin-welcome-message"),
            reply_markup=get_main_menu_keyboard(user_role="admin"),
        )
