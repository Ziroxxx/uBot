import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties

#Для отравки сообщений по времени
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from timoutHandlers import register_handlers, setup_scheduler

import config
from handlers import router

scheduler = AsyncIOScheduler()

async def main():
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Заменено
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    setup_scheduler(scheduler, bot)  # ✅ Настраиваем планировщик
    scheduler.start()
    register_handlers(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())