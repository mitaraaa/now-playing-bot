# Spotify Now Playing Telegram Bot

This bot allows you to share your recently played Spotify tracks in Telegram.

Try it out: [@spotifynpbot](https://t.me/spotifynpbot)

## Features

- Fetch recently played tracks from Spotify
- Add tracks to the queue
- Inline mode
- Logging

## Usage

To launch the bot, you need to create a Spotify app [(link)](https://developer.spotify.com/dashboard/create) and a Telegram bot [(BotFather)](https://t.me/botfather).

After that, you need to set the following environment variables:

### Environment variables

Create a `.env` file in the root directory with the following content:

```properties
MODE=polling or webhook

# for webhook
HOST=your-domain.com
PORT=3000

# you need to whitelist this in Spotify dashboard
REDIRECT_URI=http://your-domain.com/callback

SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret

REDIS_HOST=redis  # docker-compose service name/localhost
REDIS_PORT=6379
REDIS_USER=your-redis-user
REDIS_PASSWORD=your-redis-password

CALLBACK_PORT=80 # or any port you want, as long as it matches redirect_uri

BOT_TOKEN=your-telegram-bot-token

APP_CONTAINER=now-playing-app  # or any name you want
APP_IMAGE=mitaraaa/now-playing-app:1  # or your custom image

DB_CONTAINER=redis  # or any name you want
DB_IMAGE=redis/redis-stack:7.2.0-v3  # tested with this version
```

### Start

To start the bot, run the following commands:

```sh
poetry install
python -m src.main
```

This will start the bot with the mode specified in the `.env` file.

### Start with Docker

To start the bot with Docker, run the following commands:

```sh
docker build -t mitaraaa/now-playing-app:1 .
docker compose up
```

This will start the bot and Redis with the configuration specified in the `docker-compose.yaml` file.

## Inspiration

This project was inspired by [@nowplaybot](https://t.me/nowplaybot) and the need to share my recently played tracks with my friends.

Also, I used [buurro/spotify-now-playing-telegram](https://github.com/buurro/spotify-now-playing-telegram) as a reference.

## Things to consider

This project is still in development, and there are some things to consider:

- Possible rate limiting from Spotify
- Managing high traffic
- Statistics for each user (e.g., how many times a user has shared a track)
- Support for Yandex Music/Apple Music/Last.fm/etc.
- More features like sharing playlists, searching for tracks
- Better logging

## References

- [Spotify API](https://developer.spotify.com/documentation/web-api/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram](https://docs.aiogram.dev/en/latest/)
- [tornado](https://www.tornadoweb.org/en/stable/)
- [redis-py](https://redis-py.readthedocs.io/en/stable/)
- [docker-compose](https://docs.docker.com/compose/)
- [poetry](https://python-poetry.org/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
