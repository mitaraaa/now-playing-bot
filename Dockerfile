FROM python:3.11.3-slim-buster

WORKDIR /app

RUN apt update

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-root

COPY ./src ./src