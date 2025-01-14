import os

from logzero import logger
from slack_bolt.async_app import AsyncApp

from slack_youtube_dl_bot.process_message import process_message

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])


@app.message("")
async def receive_message(message, say):
    logger.debug(f"Received a message: {message}")

    await process_message(message=message, say=say)
