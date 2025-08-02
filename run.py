import asyncio
import logging

from aiogram import Bot, Dispatcher
from app.handlers import router
from commands import BOT_COMMANDS
from config import TOKEN
from app.database.models import async_main



async def main():
    await async_main()
    print("🤖 Бот запущен...")
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router)
    await bot.set_my_commands(BOT_COMMANDS)
    await  dp.start_polling(bot)





if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен')

