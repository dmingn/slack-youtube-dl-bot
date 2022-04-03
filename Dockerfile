FROM python:3.10-slim AS builder

WORKDIR /slack-youtube-dl-bot

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

FROM python:3.10-slim

WORKDIR /slack-youtube-dl-bot

# TODO: reduce image size
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

COPY slack_youtube_dl_bot ./slack_youtube_dl_bot

ENTRYPOINT ["python", "-m", "slack_youtube_dl_bot"]
