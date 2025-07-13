# database/services/captcha_service.py

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CaptchaSession, CaptchaSetting
from ..repository import CaptchaSessionRepository, CaptchaSettingRepository


class CaptchaService:
    """Сервис для работы с настройками и сессиями каптчи"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.captcha_setting_repo = CaptchaSettingRepository(session)
        self.captcha_session_repo = CaptchaSessionRepository(session)

    async def get_captcha_settings(self, group_id: int) -> CaptchaSetting | None:
        """Получение настроек каптчи для группы"""
        return await self.captcha_setting_repo.get_by_group_id(group_id)

    async def create_default_captcha_settings(self, group_id: int) -> CaptchaSetting:
        """Создание настроек каптчи по умолчанию для новой группы"""
        return await self.captcha_setting_repo.create(
            group_id=group_id,
            captcha_type="standard",
            captcha_size=2,
            difficulty_level=3,
            timeout_seconds=300,
            auto_kick_on_fail=True,
            max_attempts=3,
        )

    async def update_captcha_setting(
        self, group_id: int, setting_name: str, value
    ) -> bool:
        """Обновление конкретной настройки каптчи для группы"""
        return await self.captcha_setting_repo.update_by_column_name(
            group_id, setting_name, value
        )

    async def update_captcha_settings(
        self, group_id: int, settings_data: dict
    ) -> CaptchaSetting | None:
        """Обновление настроек каптчи для группы"""
        captcha_settings = await self.captcha_setting_repo.get_by_group_id(group_id)
        if not captcha_settings:
            # Создаем настройки, если их нет
            captcha_settings = await self.create_default_captcha_settings(group_id)

        return await self.captcha_setting_repo.update(captcha_settings, **settings_data)

    async def create_captcha_session(
        self,
        user_id: int,
        group_id: int,
        question: str,
        correct_answer: str,
        expires_at: datetime,
        message_id: int | None = None,
    ) -> CaptchaSession:
        """Создание новой сессии каптчи"""
        # Получаем настройки каптчи для группы
        captcha_settings = await self.captcha_setting_repo.get_by_group_id(group_id)
        if not captcha_settings:
            raise ValueError(f"CAPTCHA settings not found for group {group_id}")

        # Удаляем существующую сессию, если есть
        existing_session = await self.captcha_session_repo.get_by_user_and_group(
            user_id, group_id
        )
        if existing_session:
            await self.captcha_session_repo.delete(existing_session)

        # Создаем новую сессию
        return await self.captcha_session_repo.create(
            user_id=user_id,
            group_id=group_id,
            captcha_setting_id=captcha_settings.id,
            question=question,
            correct_answer=correct_answer,
            expires_at=expires_at,
            message_id=message_id,
        )

    async def get_captcha_session(
        self, user_id: int, group_id: int
    ) -> CaptchaSession | None:
        """Получение активной сессии каптчи"""
        return await self.captcha_session_repo.get_by_user_and_group(user_id, group_id)

    async def update_captcha_session(
        self, session: CaptchaSession, **kwargs
    ) -> CaptchaSession:
        """Обновление сессии каптчи"""
        return await self.captcha_session_repo.update(session, **kwargs)

    async def complete_captcha_session(
        self, user_id: int, group_id: int, success: bool = True
    ) -> bool:
        """Завершение сессии каптчи"""
        session = await self.captcha_session_repo.get_by_user_and_group(
            user_id, group_id
        )
        if not session:
            return False

        status = "completed" if success else "failed"
        await self.captcha_session_repo.update(
            session, status=status, completed_at=func.now()
        )
        return True

    async def increment_captcha_attempts(
        self, user_id: int, group_id: int
    ) -> tuple[bool, int]:
        """Увеличение количества попыток. Возвращает (превышен_лимит, текущие_попытки)"""
        session = await self.captcha_session_repo.get_by_user_and_group(
            user_id, group_id
        )
        if not session:
            return False, 0

        new_attempts = session.attempts_made + 1
        await self.captcha_session_repo.update(session, attempts_made=new_attempts)

        # Получаем настройки для проверки лимита
        captcha_settings = await self.captcha_setting_repo.get_by_id(
            session.captcha_setting_id
        )
        max_attempts = captcha_settings.max_attempts if captcha_settings else 3

        return new_attempts >= max_attempts, new_attempts

    async def cleanup_expired_sessions(self) -> int:
        """Очистка истекших сессий каптчи"""
        return await self.captcha_session_repo.cleanup_expired_sessions()

    async def get_active_sessions_count(self, group_id: int) -> int:
        """Получение количества активных сессий в группе"""
        sessions = await self.captcha_session_repo.get_active_sessions_by_group(
            group_id
        )
        return len(sessions)

    async def delete_captcha_session(self, user_id: int, group_id: int) -> bool:
        """Удаление сессии каптчи"""
        session = await self.captcha_session_repo.get_by_user_and_group(
            user_id, group_id
        )
        if not session:
            return False

        await self.captcha_session_repo.delete(session)
        return True
