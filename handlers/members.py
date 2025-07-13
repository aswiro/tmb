from aiogram import F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import IS_ADMIN, IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from config import Settings
from database.models.user import MemberStatus
from database.unit_of_work import UnitOfWork
from loguru import logger


router = Router()
router.chat_member.filter(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))


@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_ADMIN))
async def member_to_admin(
    event: ChatMemberUpdated,
    uow: UnitOfWork,
    settings: Settings,
):
    """Обрабатывает изменения статуса участника в группе в администратора."""
    # Добавляем пользователя в группу как администратора
    await uow.group_service.add_user_to_group(
        user_id=event.from_user.id, group_id=event.chat.id, status=MemberStatus.ADMIN
    )
    settings.bot_admin_ids.append(event.from_user.id)
    logger.debug(
        f"Member {event.from_user.full_name} change in chat {event.chat.title} to admin"
    )


@router.chat_member(ChatMemberUpdatedFilter(IS_ADMIN >> IS_MEMBER))
async def admin_to_member(
    event: ChatMemberUpdated,
    uow: UnitOfWork,
    settings: Settings,
):
    """Обрабатывает изменения статуса участника в группе."""
    # Добавляем пользователя в группу как администратора
    await uow.group_service.add_user_to_group(
        user_id=event.from_user.id, group_id=event.chat.id, status=MemberStatus.MEMBER
    )
    settings.bot_admin_ids.remove(event.from_user.id)
    logger.debug(
        f"Admin {event.from_user.full_name} change in chat {event.chat.title} to member"
    )


@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def member_left(
    event: ChatMemberUpdated,
    uow: UnitOfWork,
):
    """Обрабатывает выход участника из группы."""
    # Удаляем пользователя из группы с проверкой условий для полного удаления
    success = await uow.group_service.remove_user_from_group(
        user_id=event.from_user.id, group_id=event.chat.id
    )

    if success:
        logger.debug(
            f"Member {event.from_user.full_name} left chat {event.chat.title} and was processed"
        )
    else:
        logger.warning(
            f"Failed to process member {event.from_user.full_name} leaving chat {event.chat.title}"
        )


@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def member_updated(
    event: ChatMemberUpdated,
    uow: UnitOfWork,
):
    """Обрабатывает изменения статуса участника в группе в администратора."""
    # Добавляем пользователя в группу как администратора
    await uow.user_service.create_or_update_user(event.from_user)
    await uow.group_service.add_user_to_group(
        user_id=event.from_user.id, group_id=event.chat.id, status=MemberStatus.MEMBER
    )
    logger.debug(
        f"Member {event.from_user.full_name} change in chat {event.chat.title} to admin"
    )
