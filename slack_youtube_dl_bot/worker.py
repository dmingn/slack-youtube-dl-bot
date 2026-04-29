import asyncio

from logzero import logger

from slack_youtube_dl_bot.job import Job, job_queue
from slack_youtube_dl_bot.yt_dlp_cmd import build_yt_dlp_cmd

POST_INTERVAL_SECONDS = 10.0


async def process_job(job: Job, worker_id: int) -> None:
    message_prefix = f"[worker-{worker_id}] "
    message_buffer: list[str] = []

    logger.debug(f"Start downloading {job.url}")

    cmd = build_yt_dlp_cmd(url=str(job.url))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def flush_buffer() -> None:
        if not message_buffer:
            return
        content = "".join(message_buffer)
        message_buffer.clear()
        await job.reply(content)

    if proc.stdout and proc.stderr:
        while True:
            if proc.stdout.at_eof() and proc.stderr.at_eof():
                break

            stdout = (await proc.stdout.readline()).decode()
            if stdout:
                logger.debug(stdout)
                message_buffer.append(message_prefix + stdout)
            stderr = (await proc.stderr.readline()).decode()
            if stderr:
                logger.debug(stderr)
                message_buffer.append(message_prefix + stderr)

            await flush_buffer()
            await asyncio.sleep(POST_INTERVAL_SECONDS)

        await flush_buffer()

    await proc.communicate()

    logger.debug(f"Finish downloading {job.url}")


async def worker(id: int):
    logger.debug(f"Start worker-{id}")

    while True:
        job = await job_queue.get()

        await process_job(job=job, worker_id=id)

        job_queue.task_done()
