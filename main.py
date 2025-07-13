import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import I18n
from cache import redis_client
from config.admin_list import AdminManager
from config.settings import settings
from database import _db as db
from database.unit_of_work import UnitOfWork
from handlers import setup_routers
from loguru import logger
from middlewares import DbSessionMiddleware, I18nMiddleware


async def main():
    # Инициализация базы данных при запуске приложения
    await db.initialize()
    await db.init_db()

    # Инициализация Redis
    await redis_client.connect()
    logger.info("Redis initialized")

    # Обновление списка администраторов из БД
    async with db.get_session() as session:
        uow = UnitOfWork(session)
        admin_manager = AdminManager(uow)
        await admin_manager.update_admin_ids_in_settings(settings)
    logger.info(f"Admin IDs loaded from database: {settings.bot_admin_ids}")

    # Bot
    bot = Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    # Инициализация хранилища состояний
    storage = RedisStorage(redis_client.redis)

    # Инициализация диспетчера
    dp = Dispatcher(storage=storage)
    i18n = I18n(path="locales", default_locale="en", domain="messages")

    # Регистрация middleware

    dp.update.middleware(DbSessionMiddleware(db))
    dp.update.middleware(I18nMiddleware(i18n))

    # Инициализация роутеров
    await setup_routers(dp)

    dp["settings"] = settings
    # Запускаем бота
    logger.info("Starting bot")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            skip_updates=True,
        )
    finally:
        # Закрываем соединения при завершении
        await db.close()
        await redis_client.disconnect()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
