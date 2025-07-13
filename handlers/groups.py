import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from config import Settings
from database.models.user import MemberStatus
from database.unit_of_work import UnitOfWork
from keyboards.buttons import get_main_menu_keyboard
from keyboards.group import (
    GroupCallbackFactory,
    get_group_management_keyboard,
    get_groups_list_keyboard,
)
from loguru import logger


router = Router()


class GroupStates(StatesGroup):
    waiting_for_group_id = State()
    id_to_remove = State()


@router.callback_query(GroupCallbackFactory.filter(F.action == "list"))
async def on_group_list_callback(
    callback: CallbackQuery,
    uow: UnitOfWork,
):
    """Обработчик нажатия на кнопку 'Мои группы'"""
    await callback.answer()
    try:
        await show_user_groups(callback.message, uow)
    except Exception as e:
        logger.exception("Ошибка при запросе списка групп", exc_info=e)
        await callback.message.answer(_("error-getting-groups"))


async def show_user_groups(message: Message, uow: UnitOfWork):
    """Показывает список групп пользователя."""
    async with uow:
        groups = await uow.group_service.get_all_groups()

    if not groups:
        await message.edit_text(
            _("groups-list-empty"), reply_markup=get_group_management_keyboard()
        )
        return

    groups_text = _("all-groups-header")

    await message.edit_text(groups_text, reply_markup=get_groups_list_keyboard(groups))
    logger.info(f"Пользователь {message.from_user.id} запросил список групп")


@router.callback_query(GroupCallbackFactory.filter(F.action == "add"))
async def on_add_group_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Обработчик нажатия на кнопку 'Добавить группу'"""
    await callback.answer()
    await show_add_group_instructions(callback.message, state)


async def show_add_group_instructions(message: Message, state: FSMContext):
    """Показывает инструкции по добавлению группы."""
    await message.answer(_("add-group-instructions"))
    await state.set_state(GroupStates.waiting_for_group_id)
    logger.info(f"Пользователь {message.from_user.id} запросил добавление группы")


@router.message(GroupStates.waiting_for_group_id)
async def group_add_second(
    message: Message,
    state: FSMContext,
    uow: UnitOfWork,
    settings: Settings,
):
    """Обрабатывает ввод ID/ссылки/username, добавляет группу и админов."""
    group_input = message.text.strip() if message.text else ""
    if not re.match(r"^-\d+$|^https://t\.me/|^@", group_input):
        await message.answer(_("invalid-group-format"))
        return

    group_id_or_username = group_input
    if group_input.startswith("https://t.me/"):
        group_id_or_username = group_input.replace("https://t.me/", "@")

    # Отправляем сообщение о начале процесса
    processing_message = await message.answer(_("getting-group-info"))

    try:
        logger.debug(f"Attempting to get chat info for '{group_id_or_username}'")
        chat_info = await message.bot.get_chat(group_id_or_username)
        logger.debug(f"Got chat info: id={chat_info.id}, title='{chat_info.title}'")

        # Обновляем сообщение о статусе
        await message.bot.edit_message_text(
            _("getting-admins-list"),
            message.chat.id,
            processing_message.message_id,
        )

        # Получаем администраторов группы
        admins_raw = await message.bot.get_chat_administrators(chat_info.id)
        admins = [admin.user for admin in admins_raw if not admin.user.is_bot]
        logger.debug(f"Found {len(admins)} non-bot administrators.")

        # Обновляем сообщение о статусе
        await message.bot.edit_message_text(
            _("saving-to-database"),
            message.chat.id,
            processing_message.message_id,
        )

        async with uow:
            # Создаем или обновляем группу через сервис
            await uow.group_service.create_or_update_group(chat_info)

            # Добавляем администраторов
            admin_count = 0
            for admin in admins:
                # Создаем пользователя, если он не существует
                existing = await uow.user_service.get_user_by_id(admin.id)
                if not existing:
                    await uow.user_service.create_user(admin)

                # Добавляем пользователя в группу как администратора
                await uow.group_service.add_user_to_group(
                    user_id=admin.id, group_id=chat_info.id, status=MemberStatus.ADMIN
                )
                admin_count += 1
                settings.bot_admin_ids.append(admin.id)

            # Обновляем список администраторов
            settings.bot_admin_ids = list(set(settings.bot_admin_ids))

            await uow.filter_service.create_default_filters(chat_info.id)

            await uow.commit()

        await state.clear()
        # Удаляем сообщение о статусе
        await message.bot.delete_message(message.chat.id, processing_message.message_id)

        # Формируем подробное сообщение об успехе
        username = f"@{chat_info.username}" if chat_info.username else _("no-username")
        success_message = _("group-added-success").format(
            title=chat_info.title,
            id=chat_info.id,
            username=username,
            admin_count=admin_count,
        )
        groups = await uow.group_service.get_all_groups()
        await message.answer(
            success_message, reply_markup=get_groups_list_keyboard(groups)
        )
        logger.info(
            f"Группа {chat_info.title} (ID: {chat_info.id}) успешно добавлена пользователем {message.from_user.id}"
        )
    except Exception as e:
        # Удаляем сообщение о статусе, если оно существует
        await message.bot.delete_message(message.chat.id, processing_message.message_id)

        logger.exception(
            f"Ошибка при добавлении группы {group_id_or_username}", exc_info=e
        )

        # Добавляем более информативное сообщение в зависимости от типа ошибки
        if "chat not found" in str(e).lower():
            error_message = _("error-chat-not-found")
        elif "bot is not a member" in str(e).lower():
            error_message = _("error-bot-not-member")
        elif "not enough rights" in str(e).lower() or "permission" in str(e).lower():
            error_message = _("error-insufficient-rights")
        else:
            error_message = _("error-adding-group").format(error=str(e))

        await message.answer(
            error_message, reply_markup=get_main_menu_keyboard(user_role="admin")
        )
        await state.clear()


@router.callback_query(GroupCallbackFactory.filter(F.action == "remove"))
async def on_remove_group_callback(
    callback: CallbackQuery,
    callback_data: GroupCallbackFactory,
    state: FSMContext,
    uow: UnitOfWork,
):
    """Обработчик нажатия на кнопку удаления конкретной группы"""
    await callback.answer()
    group_id = callback_data.group_id

    try:
        await remove_group_by_id(
            callback.message, int(group_id), state, uow, is_callback=True
        )
    except Exception as e:
        logger.exception(f"Ошибка при удалении группы {group_id}", exc_info=e)

        # Добавляем более информативное сообщение в зависимости от типа ошибки
        if "not found" in str(e).lower():
            error_message = _("error-group-not-found")
        elif "permission" in str(e).lower() or "access" in str(e).lower():
            error_message = _("error-insufficient-permissions")
        elif "constraint" in str(e).lower() or "foreign key" in str(e).lower():
            error_message = _("error-cannot-remove-related-data")
        else:
            error_message = _("error-removing-group").format(error=str(e))

        await callback.message.answer(error_message)
        await state.clear()


async def remove_group_by_id(
    message: Message,
    group_id: int,
    state: FSMContext,
    uow: UnitOfWork,
    is_callback: bool = False,
):
    """Удаляет группу по ID с проверкой прав пользователя"""
    async with uow:
        # Проверяем существование группы
        group = await uow.group_service.get_group_by_id(group_id)
        if group:
            logger.info(f"Group list: {group.title}")
        if not group:
            await message.answer(_("group-not-found"))
            await state.clear()
            return

        group_title = group.title  # Сохраняем название группы до удаления
        username = f"@{group.username}" if group.username else _("no-username")

        # Удаляем группу и всех её участников
        success = await uow.group_service.delete_group(group_id)
        if not success:
            await message.answer(_("failed-to-remove-group"))
            await state.clear()
            return

        await uow.commit()

    # Формируем подробное сообщение об успешном удалении
    success_message = _("group-removed-success").format(
        title=group_title, id=group_id, username=username
    )
    groups = await uow.group_service.get_all_groups()
    if is_callback:
        await message.edit_text(
            success_message, reply_markup=get_groups_list_keyboard(groups)
        )
    else:
        await message.answer(success_message)

    logger.info(
        f"Группа {group_title} (ID: {group_id}) успешно удалена пользователем {message.from_user.id}"
    )
