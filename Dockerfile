FROM python:3.10-slim AS builder

WORKDIR /workdir

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv sync --locked --no-dev

FROM alpine:latest AS ffmpeg-downloader

WORKDIR /workdir

RUN apk add --no-cache curl

RUN curl -L https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz | tar -Jxf -

FROM python:3.10-slim

RUN groupadd -g 1000 appgroup && \
    useradd -m -u 1000 -g appgroup appuser

WORKDIR /workdir

COPY --from=ffmpeg-downloader /workdir/ffmpeg-master-latest-linux64-gpl/bin /usr/local/bin

COPY --from=builder /workdir/.venv /workdir/.venv

COPY slack_youtube_dl_bot ./slack_youtube_dl_bot

ENV PATH="/workdir/.venv/bin:$PATH"

ENTRYPOINT ["python", "-m", "slack_youtube_dl_bot"]
