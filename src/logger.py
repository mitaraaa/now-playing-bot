import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    return logger.getChild(name)
