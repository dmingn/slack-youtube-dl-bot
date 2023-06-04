import asyncio
import dataclasses
import os
from functools import partial
from typing import Any

import click
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])


@dataclasses.dataclass(frozen=True)
class Job:
    message: dict[str, Any]
    say: AsyncSay

    @property
    def url(self) -> str:
        # TODO: text の mrkdwn 形式から plain_text 形式への変換をちゃんとやる
        # NOTE: https://api.slack.com/reference/surfaces/formatting
        return self.message["text"].strip("<>")

    @property
    def reply(self):
        return partial(self.say, thread_ts=self.message["ts"])


job_queue: asyncio.Queue[Job] = asyncio.Queue()


async def say_job_queue(say: AsyncSay):
    if job_queue.empty:
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
    job = Job(message=message, say=say)

    await job_queue.put(job)

    await job.reply(f"{job.url} is pushed to the job queue.")

    await say_job_queue(job.say)


async def download(job: Job, message_prefix: str = "") -> None:
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
                await job.reply(message_prefix + stdout)
            stderr = (await proc.stderr.readline()).decode()
            if stderr:
                await job.reply(message_prefix + stderr)

            await asyncio.sleep(1)

    await proc.communicate()


async def worker(id: int):
    while True:
        job = await job_queue.get()

        await say_job_queue(job.say)

        await download(job, message_prefix=f"[worker-{id}] ")

        job_queue.task_done()


async def main(n_workers: int):
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
