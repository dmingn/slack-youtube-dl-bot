import asyncio
import os
from functools import partial

import click
from logzero import logger
from pydantic.dataclasses import dataclass
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])


def extract_url_from_message_text(text: str) -> str:
    # TODO: text の mrkdwn 形式から plain_text 形式への変換をちゃんとやる
    # NOTE: https://api.slack.com/reference/surfaces/formatting
    return text.strip("<>")


@dataclass(frozen=True)
class Job:
    url: str
    thread_ts: str
    say: AsyncSay

    @property
    def reply(self):
        return partial(self.say, thread_ts=self.thread_ts)


job_queue: asyncio.Queue[Job] = asyncio.Queue()


async def say_job_queue(say: AsyncSay):
    if job_queue.empty():
        await asyncio.sleep(0)
    else:
        await say(
            "\n".join(
                [
                    "--- Current job queue ---",
                ]
                + [f"{i+1}: {job.url}" for i, job in enumerate(job_queue._queue)]
            )
        )


@app.message("")
async def receive_url(message, say):
    logger.debug(f"Received a message: {message}")

    job = Job(
        url=extract_url_from_message_text(message["text"]),
        thread_ts=message["ts"],
        say=say,
    )

    await job_queue.put(job)

    logger.debug(f"{job.url} is pushed to the job queue.")
    await job.reply(f"{job.url} is pushed to the job queue.")

    await say_job_queue(job.say)


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

        await say_job_queue(job.say)

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
