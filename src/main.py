import asyncio

import tornado
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp.web import Application, run_app

from src.bot import bot, dp
from src.config import Config
from src.logger import get_logger
from src.web.handlers import urls

logger = get_logger("main")


async def start_bot():
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Authenticate with Spotify"),
            BotCommand(command="logout", description="Log out of Spotify"),
        ]
    )

    logger.info("Starting bot")

    if Config.MODE == "webhook":
        aioapp = Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=Config.BOT_TOKEN,
        )
        webhook_requests_handler.register(app, path=Config.HOST)
        setup_application(app, dp, bot=bot)
        run_app(aioapp, host=Config.HOST, port=Config.PORT)
    else:
        await dp.start_polling(bot)


async def start_web():
    web = tornado.web.Application(urls)
    web.listen(Config.CALLBACK_PORT)

    logger.info(f"Server started at {Config.HOST}, port {Config.CALLBACK_PORT}")

    await asyncio.Event().wait()


async def app():
    # Start the bot and web server concurrently
    asyncio.create_task(start_bot())
    await start_web()


if __name__ == "__main__":
    asyncio.run(app())
