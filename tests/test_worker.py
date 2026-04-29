import sys

import pytest
from slack_bolt.context.say.async_say import AsyncSay

from slack_youtube_dl_bot.job import Job
from slack_youtube_dl_bot.worker import POST_INTERVAL_SECONDS, process_job


class _RecordingSay(AsyncSay):
    def __init__(self):
        super().__init__(client=None, channel="C_TEST", thread_ts=None)
        self.calls: list[dict] = []

    async def __call__(self, text="", thread_ts=None, **kwargs):
        self.calls.append({"text": text, "thread_ts": thread_ts, "kwargs": kwargs})


class _FakeStream:
    def __init__(self, lines: list[bytes]):
        self._lines = lines
        self._idx = 0

    def at_eof(self) -> bool:
        return self._idx >= len(self._lines)

    async def readline(self) -> bytes:
        if self.at_eof():
            return b""
        line = self._lines[self._idx]
        self._idx += 1
        return line


class _FakeProc:
    def __init__(self, stdout_lines: list[bytes], stderr_lines: list[bytes]):
        self.stdout = _FakeStream(stdout_lines)
        self.stderr = _FakeStream(stderr_lines)

    async def communicate(self):
        return (b"", b"")


@pytest.mark.asyncio
async def test_process_job_happy_path_posts_buffered_subprocess_output_to_slack(
    monkeypatch,
):
    say = _RecordingSay()
    job = Job(url="https://example.com/video", thread_ts="123.456", say=say)

    created: dict = {}

    async def fake_create_subprocess_exec(*cmd, stdout=None, stderr=None):
        created["cmd"] = tuple(cmd)
        created["stdout"] = stdout
        created["stderr"] = stderr
        return _FakeProc(
            stdout_lines=[b"hello-stdout\n"], stderr_lines=[b"hello-stderr\n"]
        )

    sleep_calls: list[float] = []

    async def fake_sleep(seconds: float):
        sleep_calls.append(seconds)
        return None

    monkeypatch.setattr(
        "slack_youtube_dl_bot.worker.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    monkeypatch.setattr("slack_youtube_dl_bot.worker.asyncio.sleep", fake_sleep)

    await process_job(job=job, worker_id=7)

    assert created["cmd"][:3] == (sys.executable, "-m", "yt_dlp")
    assert "https://example.com/video" in created["cmd"]

    texts = [c["text"] for c in say.calls]
    assert texts == ["[worker-7] hello-stdout\n[worker-7] hello-stderr\n"]
    assert sleep_calls == [POST_INTERVAL_SECONDS]
