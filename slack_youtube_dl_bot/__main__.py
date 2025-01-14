import asyncio
import os
import re
from functools import partial

import click
from logzero import logger
from pydantic import AnyHttpUrl, ConfigDict, ValidationError
from pydantic.dataclasses import dataclass
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])


def extract_url_from_message_text(text: str) -> str:
    # cf. https://api.slack.com/reference/surfaces/formatting#linking-urls
    url_pattern = re.compile(r"<(https?://[^>|]+)")
    match = url_pattern.search(text)
    if match:
        return match.group(1)
    return ""


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class Job:
    url: AnyHttpUrl
    thread_ts: str
    say: AsyncSay

    @property
    def reply(self):
        return partial(self.say, thread_ts=self.thread_ts)


job_queue: asyncio.Queue[Job] = asyncio.Queue()


@app.message("")
async def receive_url(message, say):
    logger.debug(f"Received a message: {message}")

    try:
        job = Job(
            url=extract_url_from_message_text(message["text"]),
            thread_ts=message["ts"],
            say=say,
        )
    except ValidationError as e:
        logger.error(e)
        await say(f"Invalid message: {message['text']}", thread_ts=message["ts"])
        await say(e, thread_ts=message["ts"])
        return

    await job_queue.put(job)

    logger.debug(f"{job.url} is pushed to the job queue.")
    await job.reply(f"{job.url} is pushed to the job queue.")


async def download(job: Job, message_prefix: str = "") -> None:
    logger.debug(f"Start downloading {job.url}")

    proc = await asyncio.create_subprocess_shell(
        " ".join(
            [
                "python",
                "-m",
                "yt_dlp",
                "-o",
                '"/out/%(extractor)s/%(channel)s - %(channel_id)s/%(playlist)s - %(playlist_id)s/%(title)s - %(id)s.%(ext)s"',
                "--no-progress",
                f'"{job.url}"',
            ]
        ),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if proc.stdout and proc.stderr:
        while True:
            if proc.stdout.at_eof() and proc.stderr.at_eof():
                break

            stdout = (await proc.stdout.readline()).decode()
            if stdout:
                logger.debug(stdout)
                await job.reply(message_prefix + stdout)
            stderr = (await proc.stderr.readline()).decode()
            if stderr:
                logger.debug(stderr)
                await job.reply(message_prefix + stderr)

            await asyncio.sleep(1)

    await proc.communicate()

    logger.debug(f"Finish downloading {job.url}")


async def worker(id: int):
    logger.debug(f"Start worker-{id}")

    while True:
        job = await job_queue.get()

        await download(job, message_prefix=f"[worker-{id}] ")

        job_queue.task_done()


async def main(n_workers: int):
    logger.debug(f"Start the bot with {n_workers} workers.")

    slack_bot = asyncio.create_task(
        AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start_async()
    )

    workers = [asyncio.create_task(worker(i)) for i in range(n_workers)]

    await slack_bot
    await job_queue.join()
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)


@click.command()
@click.option("--n_workers", type=click.IntRange(min=1), default=1)
def cli(n_workers: int):
    asyncio.run(main(n_workers=n_workers))


if __name__ == "__main__":
    cli()
