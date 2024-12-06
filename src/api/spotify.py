import datetime
import json
from typing import Generator
from urllib.parse import urlencode

import httpx

from src.api.database import (
    delete_token,
    get_token,
    set_token,
)
from src.api.urls import SpotifyURL
from src.config import Config
from src.logger import get_logger

logger = get_logger("api.spotify")


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

        logger.debug(f"User credentials received, grant: {grant[:8]}...{grant[-8:]}")

        return response.json()

    async def get_credentials(self, user_id: str) -> dict:
        """
        Get user credentials from Redis.
        """
        credentials = get_token(user_id)

        if not credentials:
            logger.debug(f"[{user_id}]: User credentials not found")
            raise Exception("User credentials not found")

        credentials = json.loads(credentials)

        if credentials["expires_at"] < datetime.datetime.now().timestamp():
            logger.debug(f"[{user_id}]: User credentials expired")
            credentials = await self.refresh_user_credentials(
                user_id, credentials["refresh_token"]
            )

        return credentials

    async def refresh_user_credentials(self, user_id: str, refresh_token: str) -> dict:
        """
        Refresh user credentials on expire event.
        """

        delete_token(user_id)

        data = {
            "grant_type": self.REFRESH_GRANT_TYPE,
            "refresh_token": refresh_token,
        }

        logger.debug(f"[{user_id}]: Attempting to refresh token")

        response = await self.requests.post(
            SpotifyURL.TOKEN,
            data=data,
            auth=(self._client_id, self._client_secret),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        if response.status_code != 200:
            logger.debug(f"[{user_id}]: Failed to refresh token")
            return

        new = response.json()
        new["refresh_token"] = refresh_token

        set_token(user_id, new)
        logger.debug(f"[{user_id}]: Token refreshed")

        return new

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
        credentials = await self.get_credentials(user_id)

        if not credentials:
            logger.debug(f"[{user_id}]: User credentials not found")
            raise Exception("User credentials not found")

        response = await self.requests.post(
            SpotifyURL.ADD_TO_QUEUE,
            headers={
                "Authorization": f"Bearer {credentials['access_token']}",
            },
            params={"uri": uri},
        )

        logger.debug(f"[{user_id}]: Added track to queue ({uri})")

        if response.status_code != 204:
            logger.debug(f"[{user_id}]: Failed to add track to queue ({uri})")
            raise Exception("Failed to add track to queue")

    async def get_track(self, user_id: str, track_id: str) -> dict:
        """
        Get a track by its ID.
        """
        credentials = await self.get_credentials(user_id)

        response = await self.requests.get(
            SpotifyURL.GET_TRACK.format(
                track_id=track_id,
                headers={"Authorization": f"Bearer {credentials['access_token']}"},
            )
        )

        if response.status_code != 200:
            logger.debug(f"Failed to get track ({track_id})")
            return None

        return response.json()

    async def get_currently_playing(self, user_id: str) -> dict:
        """
        Get the currently playing track.
        """
        credentials = await self.get_credentials(user_id)

        response = await self.requests.get(
            SpotifyURL.CURRENTLY_PLAYING,
            headers={
                "Authorization": f"Bearer {credentials['access_token']}",
            },
        )

        if response.status_code != 200:
            logger.debug(f"[{user_id}]: Failed to get currently playing")
            return None

        logger.debug(f"[{user_id}]: Fetched currently playing")
        return response.json()

    async def get_recently_played(self, user_id: str) -> Generator[dict, None, None]:
        """
        Get the user's recently played tracks.
        """
        credentials = await self.get_credentials(user_id)

        if not credentials:
            logger.debug(f"[{user_id}]: User credentials not found")
            raise Exception("User credentials not found")

        response = await self.requests.get(
            SpotifyURL.RECENTLY_PLAYED,
            headers={
                "Authorization": f"Bearer {credentials['access_token']}",
            },
            params={"limit": 5},
        )

        if response.status_code != 200:
            logger.debug(f"[{user_id}]: Failed to get recently played")
            raise Exception("Failed to get recently played")

        items = response.json()["items"]

        if not items:
            return []

        current = await self.get_currently_playing(user_id)

        if current and current["item"]:
            logger.debug(f"[{user_id}]: Currently playing track found")
            items.insert(0, {"track": current["item"]})

        tracks = []
        for track in map(lambda x: x["track"], items):
            if tracks and track["uri"] in map(lambda x: x["uri"], tracks):
                continue

            track = await self.get_track(user_id, track["id"])

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

        logger.debug(f"[{user_id}]: Fetched recently played tracks ({len(tracks)})")
        return tracks


client = SpotifyClient(
    redirect_uri=Config.REDIRECT_URI,
    client_id=Config.SPOTIFY_CLIENT_ID,
    client_secret=Config.SPOTIFY_CLIENT_SECRET,
    scopes=Config.SCOPES,
)
