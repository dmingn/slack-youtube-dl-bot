FROM python:3.10-slim

WORKDIR /slack-youtube-dl-bot

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install

ENTRYPOINT ["bash"]
