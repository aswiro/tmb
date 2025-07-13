# database/services/advertiser_service.py

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Advertiser
from ..repository import AdvertiserRepository


class AdvertiserService:
    """Сервис для работы с рекламодателями"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.advertiser_repo = AdvertiserRepository(session)

    async def create_advertiser(self, user_id: int, name: str) -> Advertiser:
        """Создание нового рекламодателя"""
        return await self.advertiser_repo.create(
            user_id=user_id, name=name, balance=Decimal("0.00")
        )

    async def get_advertiser(self, user_id: int) -> Advertiser | None:
        """Получение рекламодателя по ID пользователя"""
        return await self.advertiser_repo.get_by_user_id(user_id)

    async def update_advertiser(
        self, advertiser_id: int, **kwargs
    ) -> Advertiser | None:
        """Обновление данных рекламодателя"""
        advertiser = await self.advertiser_repo.get_by_id(advertiser_id)
        if not advertiser:
            return None

        return await self.advertiser_repo.update(advertiser, **kwargs)

    async def add_balance(self, user_id: int, amount: Decimal) -> Advertiser | None:
        """Пополнение баланса рекламодателя"""
        advertiser = await self.advertiser_repo.get_by_user_id(user_id)
        if not advertiser:
            return None

        new_balance = advertiser.balance + amount
        return await self.advertiser_repo.update(advertiser, balance=new_balance)

    async def deduct_balance(self, user_id: int, amount: Decimal) -> bool:
        """Списание средств с баланса рекламодателя"""
        advertiser = await self.advertiser_repo.get_by_user_id(user_id)
        if not advertiser or advertiser.balance < amount:
            return False

        new_balance = advertiser.balance - amount
        await self.advertiser_repo.update(advertiser, balance=new_balance)
        return True

    async def get_all_advertisers(self) -> list[Advertiser]:
        """Получение всех рекламодателей"""
        return await self.advertiser_repo.get_all()

    async def get_advertiser_by_id(self, advertiser_id: int) -> Advertiser | None:
        """Получение рекламодателя по ID"""
        return await self.advertiser_repo.get_by_id(advertiser_id)
