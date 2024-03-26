# Spotify Now Playing Telegram Bot

### Environment variables

```properties
MODE=polling

HOST=localhost
PORT=3000  # for webhook

REDIRECT_URI=http://localhost/callback  # should be whitelisted in Spotify app settings

SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USER=YOUR_REDIS_USER
REDIS_PASSWORD=YOUR_REDIS_PASSWORD

CALLBACK_PORT=8888  # for Tornado auth flow server

BOT_TOKEN=YOUR_BOT_TOKEN
```

### Start

```sh
poetry install
python -m src.main
```

### Redis config

```
acl list
1) user YOUR_REDIS_USER on #HASHED_PASSWORD ~* &* +@all

config set notify-keyspace-events KEA
```
