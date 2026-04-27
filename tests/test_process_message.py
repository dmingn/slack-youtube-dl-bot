import asyncio

import pytest
from slack_bolt.context.say.async_say import AsyncSay

from slack_youtube_dl_bot.process_message import (
    extract_url_from_message_text,
    process_message,
)


class _RecordingSay(AsyncSay):
    def __init__(self):
        super().__init__(client=None, channel="C_TEST", thread_ts=None)
        self.calls: list[dict] = []

    async def __call__(self, text="", thread_ts=None, **kwargs):
        self.calls.append({"text": text, "thread_ts": thread_ts, "kwargs": kwargs})


@pytest.mark.parametrize(
    "text, expected",
    [
        ("<https://example.com/path?query=1>", "https://example.com/path?query=1"),
        (
            "This message contains a URL <https://example.com/path?query=1>",
            "https://example.com/path?query=1",
        ),
        (
            "This message contains URLs <https://example.com/path?query=1> <https://example.com/path?query=2>",
            "https://example.com/path?query=1",
        ),
        (
            "<https://example.com/path?query=1|This message *is* a link>",
            "https://example.com/path?query=1",
        ),
    ],
)
def test_extract_url_from_message_text(text: str, expected: str):
    assert extract_url_from_message_text(text) == expected


@pytest.mark.asyncio
async def test_process_message_happy_path_enqueues_job_and_replies(monkeypatch):
    queue: asyncio.Queue = asyncio.Queue()

    monkeypatch.setattr("slack_youtube_dl_bot.job.job_queue", queue)
    monkeypatch.setattr("slack_youtube_dl_bot.process_message.job_queue", queue)

    say = _RecordingSay()

    message = {"text": "<https://example.com/path?query=1>", "ts": "123.456"}
    await process_message(message=message, say=say)

    job = queue.get_nowait()
    assert str(job.url) == "https://example.com/path?query=1"
    assert job.thread_ts == "123.456"

    assert len(say.calls) == 1
    assert say.calls[0]["thread_ts"] == "123.456"
    assert "https://example.com/path?query=1" in say.calls[0]["text"]
    assert "is pushed to the job queue" in say.calls[0]["text"]
