import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MODE = os.getenv("MODE", "polling")  # webhook or polling

    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")

    REDIRECT_URI = os.getenv("REDIRECT_URI")

    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_USER = os.getenv("REDIS_USER")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    BOT_TOKEN = os.getenv("BOT_TOKEN")

    CALLBACK_PORT = os.getenv("CALLBACK_PORT")

    SCOPES = "user-read-recently-played user-read-currently-playing user-modify-playback-state"
