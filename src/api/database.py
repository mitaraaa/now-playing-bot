import redis

from src.config import Config

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

    print("Subscribed to '__keyevent@0__:expired' channel")


def get_token(user_id: str) -> dict:
    return r.get(user_id)


def set_token(user_id: str, credentials: dict) -> None:
    r.set(user_id, credentials)
    r.expire(user_id, Config.TOKEN_TTL)


def delete_token(user_id: str) -> None:
    r.delete(user_id)
