FROM python:3.10-slim AS builder

WORKDIR /workdir

ENV PIPENV_HOME=/opt/pipenv

RUN python3 -m venv $PIPENV_HOME && \
    $PIPENV_HOME/bin/pip install pipenv==2023.6.2

COPY Pipfile Pipfile.lock ./

RUN $PIPENV_HOME/bin/pipenv sync --system

FROM alpine:latest AS ffmpeg-downloader

WORKDIR /workdir

RUN apk add --no-cache curl

RUN curl -L https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz | tar -Jxf -

FROM python:3.10-slim

RUN groupadd -g 1000 appgroup && \
    useradd -m -u 1000 -g appgroup appuser

WORKDIR /workdir

COPY --from=ffmpeg-downloader /workdir/ffmpeg-master-latest-linux64-gpl/bin /usr/local/bin

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

COPY slack_youtube_dl_bot ./slack_youtube_dl_bot

ENTRYPOINT ["python", "-m", "slack_youtube_dl_bot"]
