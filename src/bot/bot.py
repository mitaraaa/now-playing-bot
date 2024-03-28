from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultAudio,
    Message,
)

from src.api.database import delete_token, get_token
from src.api.spotify import client
from src.bot.keyboards import register_markup, track_markup
from src.config import Config
from src.logger import get_logger

dp = Dispatcher()
bot = Bot(Config.BOT_TOKEN)

logger = get_logger("bot")


@dp.message(CommandStart())
async def register(message: Message, command: CommandObject) -> None:
    args = command.args
    if args and args == "error":
        await message.answer("There seems to be an error, maybe try again later?")
        logger.info(f"[{message.from_user.id}] Clicked on error message")
        return

    if get_token(message.from_user.id):
        await message.answer(
            "Your account is already linked!\n\nSend /logout to unlink it"
        )
        logger.info(f"[{message.from_user.id}] User is already authenticated")
        return

    await message.answer(
        "Hello! To start using this bot, you need to authenticate with Spotify. "
        "Please, click the following link: ",
        reply_markup=register_markup(
            client.register(message.from_user.id),
        ),
    )
    logger.info(f"[{message.from_user.id}] User has started the bot")


@dp.message(Command("logout"))
async def logout(message: Message) -> None:
    user_id = message.from_user.id

    if not get_token(user_id):
        await message.answer("You are not authenticated with Spotify.")
        logger.info(f"[{user_id}] Failed to logout: not authenticated")
        return

    delete_token(user_id)

    await message.answer("You have been successfully logged out of Spotify.")
    logger.info(f"[{user_id}] User has logged out of Spotify")


@dp.inline_query()
async def recently_played(inline_query: InlineQuery) -> None:
    user_id = inline_query.from_user.id

    if not get_token(user_id):
        await inline_query.answer(
            results=[],
            switch_pm_text="Authenticate with Spotify",
            switch_pm_parameter="reauth",
            cache_time=10,
            is_personal=True,
        )
        logger.info(f"[{user_id}] User is not authenticated with Spotify")
        return

    try:
        tracks = await client.get_recently_played(user_id)
    except Exception:
        await inline_query.answer(
            [],
            switch_pm_text="Failed to fetch recently played tracks",
            switch_pm_parameter="retry",
            is_personal=True,
            cache_time=2,
        )
        logger.info(f"[{user_id}] Failed to fetch recently played tracks")
        return

    results = [
        InlineQueryResultAudio(
            type="audio",
            id=track["uri"],
            title=track["name"],
            performer=track["artists"],
            audio_url=track["preview_url"] if track["preview_url"] else "",
            audio_duration=30 if track["preview_url"] else 1,
            reply_markup=track_markup(track["url"], track["uri"]),
            caption="Failed to load track preview :("
            if not track["preview_url"]
            else None,
        )
        for track in tracks
    ]

    await inline_query.answer(results=results, cache_time=5, is_personal=True)
    logger.info(f"[{user_id}] Fetched recently played tracks")


@dp.callback_query()
async def add_to_queue(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if not get_token(user_id):
        await callback_query.answer("You are not authenticated with Spotify.")
        return

    track_id = callback_query.data

    try:
        await client.add_to_queue(user_id, track_id)
    except Exception as e:
        await callback_query.answer(f"Failed to add track to queue: {e}")
        return

    await callback_query.answer("Track has been successfully added to queue.")
