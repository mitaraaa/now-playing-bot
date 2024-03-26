from aiogram.utils.keyboard import InlineKeyboardBuilder


def register_markup(url: str):
    builder = InlineKeyboardBuilder()

    builder.button(text="Authenticate with Spotify", url=url)

    return builder.as_markup()


def track_markup(url: str, add_to_queue: str):
    builder = InlineKeyboardBuilder()

    builder.button(text="View in Spotify", url=url)
    builder.button(text="Add to queue", callback_data=add_to_queue)

    return builder.as_markup()
