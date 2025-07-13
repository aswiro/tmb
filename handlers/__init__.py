from aiogram import Dispatcher

from .admins import router as admins_router
from .ads import router as ads_router
from .captcha import router as captcha_router
from .filters import router as filters_router
from .groups import router as groups_router
from .language import router as language_router
from .members import router as members_router
from .users import router as users_router


async def setup_routers(dp: Dispatcher):
    """Include all routers in the dispatcher."""
    dp.include_router(admins_router)
    dp.include_router(users_router)
    dp.include_router(groups_router)
    dp.include_router(language_router)
    dp.include_router(members_router)
    dp.include_router(filters_router)
    dp.include_router(captcha_router)
    dp.include_router(ads_router)


__all__ = [
    "setup_routers",
]
