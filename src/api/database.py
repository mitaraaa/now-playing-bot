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
r.config_set("notify-keyspace-events", "KEA")


def subscribe_to_expire_event(callback: callable) -> None:
    """
    Handles expiration of access tokens.
    """
    pubsub = r.pubsub()

    pubsub.psubscribe(**{"__keyevent@0__:expired": callback})
    pubsub.run_in_thread(sleep_time=0.001)

    logger.debug("Subscribed to '__keyevent@0__:expired' channel")


def get_token(user_id: str) -> dict:
    logger.debug(f"Getting token for user {user_id}")
    return r.get(user_id)


def set_token(user_id: str, credentials: dict) -> None:
    logger.debug(
        f"Setting token for user {user_id}, expires in {Config.TOKEN_TTL} seconds"
    )
    r.set(user_id, json.dumps(credentials))
    r.set("expired:" + user_id, "", ex=Config.TOKEN_TTL)


def delete_token(user_id: str) -> None:
    logger.debug(f"Deleting token for user {user_id}")
    r.delete(user_id)
