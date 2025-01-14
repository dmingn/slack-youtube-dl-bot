import re

from logzero import logger
from pydantic import ValidationError

from slack_youtube_dl_bot.job import Job, job_queue


def extract_url_from_message_text(text: str) -> str:
    # cf. https://api.slack.com/reference/surfaces/formatting#linking-urls
    url_pattern = re.compile(r"<(https?://[^>|]+)")
    match = url_pattern.search(text)
    if match:
        return match.group(1)
    return ""


async def process_message(message, say):
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
