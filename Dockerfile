# TODO: minimize image size
FROM python:3.10-slim

WORKDIR /slack-youtube-dl-bot

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY slack_youtube_dl_bot ./slack_youtube_dl_bot

ENTRYPOINT ["poetry", "run", "python", "-m", "slack_youtube_dl_bot"]
