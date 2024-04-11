import datetime
import json

import redis

from src.config import Config
from src.logger import get_logger

logger = get_logger("api.database")

r = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    username=Config.REDIS_USER,
    password=Config.REDIS_PASSWORD,
    decode_responses=True,
    charset="utf-8",
)


def get_token(user_id: str) -> dict:
    logger.debug(f"Getting token for user {user_id}")
    return r.get(user_id)


def set_token(user_id: str, credentials: dict) -> None:
    logger.debug(
        f"Setting token for user {user_id}, expires in {credentials['expires_in']} seconds"
    )

    credentials["expires_at"] = (
        datetime.datetime.now() + datetime.timedelta(seconds=credentials["expires_in"])
    ).timestamp()

    r.set(user_id, json.dumps(credentials))


def delete_token(user_id: str) -> None:
    logger.debug(f"Deleting token for user {user_id}")
    r.delete(user_id)
