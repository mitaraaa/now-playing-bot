from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
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

dp = Dispatcher()
bot = Bot(Config.BOT_TOKEN)


@dp.message(CommandStart())
async def register(message: Message) -> None:
    await message.answer(
        "Hello! To start using this bot, you need to authenticate with Spotify. "
        "Please, click the following link: ",
        reply_markup=register_markup(
            client.register(message.from_user.id),
        ),
    )


@dp.message(Command("logout"))
async def logout(message: Message) -> None:
    user_id = message.from_user.id

    if not get_token(user_id):
        await message.answer("You are not authenticated with Spotify.")
        return

    delete_token(user_id)

    await message.answer("You have been successfully logged out of Spotify.")


@dp.inline_query()
async def recently_played(inline_query: InlineQuery) -> None:
    user_id = inline_query.from_user.id

    if not get_token(user_id):
        await inline_query.answer(
            results=[],
            switch_pm_text="Authenticate with Spotify",
            switch_pm_parameter="reauth",
            cache_time=10,
        )
        return

    try:
        tracks = await client.get_recently_played(user_id)
    except Exception:
        await inline_query.answer("Failed to fetch recently played tracks.")
        return

    results = [
        InlineQueryResultAudio(
            id=track["uri"],
            title=track["name"],
            audio_url=track["preview_url"],
            audio_duration=30,
            performer=track["artists"],
            type="audio",
            reply_markup=track_markup(track["url"], track["uri"]),
        )
        for track in tracks
    ]

    await inline_query.answer(results=results, cache_time=5)


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
