import json

import tornado

from src.api.database import set_token
from src.api.spotify import client
from src.bot import bot


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
            self.write("Access denied")
            return

        grant = self.get_argument("code", "")
        state = self.get_argument("state", "")

        if not grant or not state:
            raise tornado.web.MissingArgumentError

        credentials = await client.build_user_credentials(grant)

        set_token(state, json.dumps(credentials), credentials["expires_in"])

        await bot.send_message(
            state, "You have been successfully authenticated with Spotify!"
        )

        self.write("Success! You can now close this tab.")


urls = [
    (r"/", MainHandler),
    (r"/callback", CallbackHandler),
]
