# database/services/user_service.py

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..repository import UserRepository


class UserService:
    """Сервис для работы с пользователями - бизнес-логика"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def create_user(self, telegram_user, is_bot: bool = False) -> User:
        """Creates a new user from Telegram"""

        # Создаем нового пользователя
        return await self.user_repo.create(
            id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
            is_bot=is_bot,
            last_active_at=func.now(),
        )

    async def create_or_update_user(self, telegram_user, is_bot: bool = False) -> User:
        """Creates or updates a user from Telegram"""

        # Проверяем, существует ли пользователь
        existing_user = await self.user_repo.get_by_id(telegram_user.id)

        if existing_user:
            # Обновляем существующего пользователя
            return await self.user_repo.update(
                existing_user,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                last_active_at=func.now(),
            )
        # Создаем нового пользователя
        return await self.create_user(telegram_user, is_bot)

    async def update_user(self, user_id: int, update_data: dict) -> User:
        """Обновление пользователя"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Добавляем время последней активности к данным обновления
        update_data["last_active_at"] = func.now()

        return await self.user_repo.update(user, **update_data)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Получение пользователя по ID"""
        return await self.user_repo.get_by_id(user_id)

    async def add_points(self, user_id: int, points: int) -> bool:
        """Добавление баллов пользователю"""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return False

        await self.user_repo.update(
            user,
            points=user.points + points,
            total_bonuses_earned=user.total_bonuses_earned + max(0, points),
        )

        # Здесь можно добавить логирование операции
        return True
