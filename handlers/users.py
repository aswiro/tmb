from aiogram import Router
from aiogram.filters.command import CommandStart
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from keyboards.buttons import get_main_menu_keyboard


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start для обычных пользователей"""
    user_name = message.from_user.full_name
    welcome_text = _("welcome-message").format(user_name=user_name)

    await message.answer(
        text=welcome_text, reply_markup=get_main_menu_keyboard(user_role="user")
    )
