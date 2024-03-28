import tornado

from src.api.database import set_token
from src.api.spotify import client
from src.bot import bot
from src.logger import get_logger

logger = get_logger("web")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        pass


class CallbackHandler(tornado.web.RequestHandler):
    async def get(self):
        """
        Handle authorization flow redirect from Spotify.
        See: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
        """
        if self.get_argument("error", ""):
            logger.debug(
                f"[{self.request.remote_ip}] Failed to authenticate with Spotify"
            )
            self.write("Failed to authenticate with Spotify")
            return

        grant = self.get_argument("code", "")
        state = self.get_argument("state", "")

        if not grant or not state:
            logger.debug(
                f"[{self.request.remote_ip}] Unable to authenticate: missing arguments"
            )
            raise tornado.web.MissingArgumentError

        credentials = await client.build_user_credentials(grant)

        set_token(state, credentials)

        await bot.send_message(
            state, "You have been successfully authenticated with Spotify!"
        )

        logger.debug(
            f"[{self.request.remote_ip}] User has been authenticated with Spotify ({state})"
        )
        self.write("Success! You can now close this tab.")


urls = [
    (r"/", MainHandler),
    (r"/callback", CallbackHandler),
]
