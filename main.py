print(">>> main.py начал запускаться")

import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router


logging.basicConfig(level=logging.INFO)


async def handle_ping(request):
    """Легковесный HTTP health-check для Render.com и UptimeRobot"""
    return web.Response(text="✅ DTM Math Bot is running 24/7!")


async def start_web_server(port: int):
    """Запускает aiohttp сервер на порту, предоставленном Render (переменная PORT)"""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 HTTP health-check сервер запущен на порту {port}")


async def main():
    print(">>> Функция main() запущена")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден. Проверьте переменные окружения (.env или на Render.com)")

    print(">>> BOT_TOKEN найден")

    await init_db()
    logging.info("✅ База данных инициализирована")

    bot = Bot(token=BOT_TOKEN)
    print(">>> Объект bot создан")

    dp = Dispatcher()
    dp.include_router(router)

    # Если задан PORT (Render Web Service), запускаем HTTP-сервер для успешной проверки порта
    port_str = os.getenv("PORT")
    if port_str and port_str.isdigit():
        await start_web_server(int(port_str))

    logging.info("🚀 Бот запущен в режиме polling!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    print(">>> Запускаем asyncio.run(main())")
    asyncio.run(main())
