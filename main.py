print(">>> main.py начал запускаться")

import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router


logging.basicConfig(level=logging.INFO)


async def main():
    print(">>> Функция main() запущена")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Проверь файл .env")

    print(">>> BOT_TOKEN найден")

    await init_db()
    logging.info("✅ База данных инициализирована")

    bot = Bot(token=BOT_TOKEN)
    print(">>> Объект bot создан")

    dp = Dispatcher()
    dp.include_router(router)

    logging.info("🚀 Бот запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    print(">>> Запускаем asyncio.run(main())")
    asyncio.run(main())