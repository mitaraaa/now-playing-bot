import json
import re
from typing import Generator
from urllib.parse import urlencode

import httpx

from src.api.database import get_token, set_token, subscribe_to_expire_event
from src.api.urls import SpotifyURL
from src.config import Config


class SpotifyClient:
    """
    Spotify API client, requires a host, client ID, client secret, and scopes.
    """

    AUTH_GRANT_TYPE = "authorization_code"
    REFRESH_GRANT_TYPE = "refresh_token"

    def __init__(
        self,
        *,
        redirect_uri: str = None,
        client_id: str = None,
        client_secret: str = None,
        scopes: str = None,
    ) -> None:
        if not all([redirect_uri, client_id, client_secret, scopes]):
            raise Exception("Missing required arguments")

        self.redirect_uri = redirect_uri

        self._client_id = client_id
        self._client_secret = client_secret

        self.scopes = scopes

        self.requests = httpx.AsyncClient()

        subscribe_to_expire_event(self.refresh_user_credentials)

    async def build_user_credentials(self, grant: str) -> dict:
        """
        Get user credentials from Spotify.
        """
        data = {
            "grant_type": self.AUTH_GRANT_TYPE,
            "code": grant,
            "redirect_uri": self.redirect_uri,
        }

        response = await self.requests.post(
            SpotifyURL.TOKEN,
            data=data,
            auth=(self._client_id, self._client_secret),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        response.raise_for_status()

        return response.json()

    def get_credentials(self, user_id: str) -> dict:
        """
        Get user credentials from Redis.
        """
        credentials = get_token(user_id)

        if not credentials:
            raise Exception("User credentials not found")

        return json.loads(credentials)

    def refresh_user_credentials(self, message: dict[str, str]) -> dict:
        """
        Refresh user credentials on expire event.
        """
        user_id = message["data"]
        token = get_token(message["data"])

        if not token:
            return

        refresh_token = token["refresh_token"]

        credentials = re.sub(r"\d+:", "", message["data"], count=1)
        credentials = json.loads(credentials)

        data = {
            "grant_type": self.REFRESH_GRANT_TYPE,
            "refresh_token": refresh_token,
        }

        response = httpx.post(
            SpotifyURL.TOKEN,
            data=data,
            auth=(self._client_id, self._client_secret),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        if response.status_code != 200:
            return

        new = response.json()

        set_token(user_id, json.dumps(new), expires_in=new["expires_in"])

    def register(self, user_id: str) -> str:
        """
        Register a user with Spotify.
        """
        query = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scopes,
                "state": user_id,
            }
        )

        return f"{SpotifyURL.AUTHORIZE}?{query}"

    async def add_to_queue(self, user_id: str, uri: str) -> None:
        """
        Add a track to the user's queue.
        """
        credentials = self.get_credentials(user_id)

        if not credentials:
            raise Exception("User credentials not found")

        response = await self.requests.post(
            SpotifyURL.ADD_TO_QUEUE,
            headers={
                "Authorization": f"Bearer {credentials['access_token']}",
            },
            params={"uri": uri},
        )

        if response.status_code != 204:
            raise Exception("Failed to add track to queue")

    async def get_currently_playing(self, user_id: str) -> dict:
        """
        Get the currently playing track.
        """
        credentials = self.get_credentials(user_id)

        response = await self.requests.get(
            SpotifyURL.CURRENTLY_PLAYING,
            headers={
                "Authorization": f"Bearer {credentials['access_token']}",
            },
        )

        if response.status_code != 200:
            return None

        return response.json()

    async def get_recently_played(self, user_id: str) -> Generator[dict, None, None]:
        """
        Get the user's recently played tracks.
        """
        credentials = self.get_credentials(user_id)

        response = await self.requests.get(
            SpotifyURL.RECENTLY_PLAYED,
            headers={
                "Authorization": f"Bearer {credentials['access_token']}",
            },
            params={"limit": 5},
        )

        if response.status_code != 200:
            raise Exception("Failed to get recently played")

        items = response.json()["items"]

        if not items:
            return []

        current = await self.get_currently_playing(user_id)

        if current:
            items.insert(0, {"track": current["item"]})

        tracks = []
        for track in map(lambda x: x["track"], items):
            if tracks and track["uri"] in map(lambda x: x["uri"], tracks):
                continue

            tracks.append(
                {
                    "image": track["album"]["images"][0]["url"],
                    "image_dimensions": (
                        track["album"]["images"][0]["height"],
                        track["album"]["images"][0]["width"],
                    ),
                    "name": track["name"],
                    "artists": ", ".join(
                        [artist["name"] for artist in track["artists"]]
                    ),
                    "url": track["external_urls"]["spotify"],
                    "uri": track["uri"],
                    "preview_url": track["preview_url"],
                }
            )

        return tracks


client = SpotifyClient(
    redirect_uri=Config.REDIRECT_URI,
    client_id=Config.SPOTIFY_CLIENT_ID,
    client_secret=Config.SPOTIFY_CLIENT_SECRET,
    scopes=Config.SCOPES,
)
