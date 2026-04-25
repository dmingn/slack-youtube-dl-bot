import asyncio
import os

import click
from logzero import logger
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from slack_youtube_dl_bot.job import job_queue
from slack_youtube_dl_bot.worker import worker


async def main(n_workers: int):
    logger.debug(f"Start the bot with {n_workers} workers.")

    # Defer importing Slack app until runtime so `--help` works without env vars.
    from slack_youtube_dl_bot.slack_app import app

    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    if not slack_app_token:
        raise click.ClickException("Environment variable SLACK_APP_TOKEN is required.")

    slack_bot = asyncio.create_task(
        AsyncSocketModeHandler(app, slack_app_token).start_async()
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
