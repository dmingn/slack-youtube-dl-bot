import asyncio

from logzero import logger

from slack_youtube_dl_bot.job import Job, job_queue
from slack_youtube_dl_bot.yt_dlp_cmd import build_yt_dlp_cmd


async def process_job(job: Job, worker_id: int) -> None:
    message_prefix = f"[worker-{worker_id}] "

    logger.debug(f"Start downloading {job.url}")

    cmd = build_yt_dlp_cmd(url=str(job.url))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
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

        await process_job(job=job, worker_id=id)

        job_queue.task_done()
