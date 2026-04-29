import asyncio

from logzero import logger

from slack_youtube_dl_bot.job import Job, job_queue
from slack_youtube_dl_bot.yt_dlp_cmd import build_yt_dlp_cmd

POST_INTERVAL_SECONDS = 10.0
SLACK_MESSAGE_CHAR_LIMIT = 4000


def chunk_output_lines(
    lines: list[str], max_chars: int = SLACK_MESSAGE_CHAR_LIMIT
) -> list[str]:
    chunks: list[str] = []
    current = ""

    for line in lines:
        if len(line) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for idx in range(0, len(line), max_chars):
                chunks.append(line[idx : idx + max_chars])
            continue

        if len(current) + len(line) > max_chars:
            chunks.append(current)
            current = line
            continue

        current += line

    if current:
        chunks.append(current)

    return chunks


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
        chunks = chunk_output_lines(message_buffer)
        message_buffer.clear()
        for chunk in chunks:
            await job.reply(chunk)

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
