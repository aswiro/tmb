# database/services/group_service.py

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import GroupMember, MemberStatus, UserStatus
from ..repository import GroupMemberRepository, GroupRepository, UserRepository


class GroupService:
    """Сервис для работы с группами"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.group_member_repo = GroupMemberRepository(session)
        self.user_repo = UserRepository(session)
        self.group_repo = GroupRepository(session)

    async def get_all_groups(self) -> list:
        """Получение всех групп"""
        result = await self.session.execute(select(self.group_repo.model_class))
        return result.scalars().all()

    async def create_or_update_group(self, telegram_group):
        """Создание или обновление группы"""
        group = await self.group_repo.get_by_id(telegram_group.id)

        if group:
            # Обновляем существующую группу
            return await self.group_repo.update(
                group,
                title=telegram_group.title,
                username=telegram_group.username,
                is_active=True,
            )
        # Создаем новую группу
        return await self.group_repo.create(
            id=telegram_group.id,
            title=telegram_group.title,
            username=telegram_group.username,
            is_active=True,
        )

    async def add_user_to_group(
        self, user_id: int, group_id: int, status: MemberStatus = MemberStatus.MEMBER
    ) -> GroupMember:
        """Добавление пользователя в группу"""
        existing = await self.group_member_repo.get_by_user_and_group(user_id, group_id)

        if existing:
            # Обновляем существующее членство
            return await self.group_member_repo.update(
                existing, status=status, joined_at=func.now(), left_at=None
            )
        # Создаем новое членство
        return await self.group_member_repo.create(
            user_id=user_id, group_id=group_id, status=status
        )

    async def warn_user(self, user_id: int, group_id: int) -> bool:
        """Выдача предупреждения пользователю"""
        member = await self.group_member_repo.get_by_user_and_group(user_id, group_id)
        if not member or not member.is_active_member:
            return False

        await self.group_member_repo.update(
            member, warnings_count=member.warnings_count + 1, last_warning_at=func.now()
        )

        # Если превышено количество предупреждений - банить
        if member.warnings_count >= 3:
            await self.ban_user(user_id, group_id, "Too many warnings")

        return True

    async def mute_user(
        self, user_id: int, group_id: int, duration_minutes: int
    ) -> bool:
        """Заглушка пользователя"""
        member = await self.group_member_repo.get_by_user_and_group(user_id, group_id)
        if not member:
            return False

        mute_until = datetime.now() + timedelta(minutes=duration_minutes)
        await self.group_member_repo.update(member, muted_until=mute_until)
        return True

    async def ban_user(self, user_id: int, group_id: int, reason: str = "") -> bool:
        """Бан пользователя"""
        member = await self.group_member_repo.get_by_user_and_group(user_id, group_id)
        if not member:
            return False

        await self.group_member_repo.update(
            member,
            status=MemberStatus.BANNED,
            ban_reason=reason,
            banned_until=None,  # Permanent ban
        )
        return True

    async def get_group_by_id(self, group_id: int):
        """Получение группы по ID"""
        return await self.group_repo.get_by_id(group_id)

    async def delete_group(self, group_id: int) -> bool:
        """Удаление группы и всех её участников"""
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            return False

        # Получаем всех участников группы
        members = await self.group_member_repo.get_group_members(group_id)

        # Обрабатываем каждого участника
        for member in members:
            # Получаем данные пользователя
            user = await self.user_repo.get_by_id(member.user_id)

            # Проверяем условия: нет username или is_bot равно False/None
            if user and (
                not user.username or user.is_bot is False or user.is_bot is None
            ):
                # Меняем статус пользователя на LEFT
                await self.user_repo.update(user, status=UserStatus.LEFT)
                # Также обновляем статус участника группы
                await self.group_member_repo.update(
                    member, status=MemberStatus.LEFT, left_at=func.now()
                )
            else:
                # Удаляем участника как обычно
                await self.group_member_repo.delete(member)

        # Удаляем саму группу
        await self.group_repo.delete(group)
        return True

    async def get_all_admin_ids(self) -> list[int]:
        """Получение ID всех администраторов из всех групп"""
        query = (
            select(GroupMember.user_id)
            .where(GroupMember.status.in_([MemberStatus.ADMIN, MemberStatus.CREATOR]))
            .distinct()
        )

        result = await self.session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def remove_user_from_group(self, user_id: int, group_id: int) -> bool:
        """Удаление пользователя из группы с проверкой условий для полного удаления"""
        # Получаем участника группы
        member = await self.group_member_repo.get_by_user_and_group(user_id, group_id)
        if not member:
            return False

        # Получаем данные пользователя
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # Проверяем условия: нет username или is_bot равно False/None
        if not user.username or user.is_bot is False or user.is_bot is None:
            # Удаляем пользователя из базы данных полностью
            await self.user_repo.delete(user)
        else:
            # Обновляем статус участника группы на LEFT
            await self.group_member_repo.update(
                member, status=MemberStatus.LEFT, left_at=func.now()
            )

        return True
