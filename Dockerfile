FROM python:3.10-slim AS builder

WORKDIR /workdir

ENV PIPENV_HOME=/opt/pipenv

RUN python3 -m venv $PIPENV_HOME && \
    $PIPENV_HOME/bin/pip install pipenv==2023.6.2

COPY Pipfile Pipfile.lock ./

RUN $PIPENV_HOME/bin/pipenv sync --system

FROM python:3.10-slim

WORKDIR /workdir

# TODO: reduce image size
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

COPY slack_youtube_dl_bot ./slack_youtube_dl_bot

ENTRYPOINT ["python", "-m", "slack_youtube_dl_bot"]
