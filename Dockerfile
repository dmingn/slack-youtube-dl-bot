# TODO: minimize image size
FROM python:3.10-slim

WORKDIR /slack-youtube-dl-bot

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY src ./src

ENTRYPOINT ["poetry", "run", "python", "src/slack_youtube_dl_bot/main.py"]
