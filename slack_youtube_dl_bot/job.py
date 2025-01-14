import asyncio
from functools import partial

from pydantic import AnyHttpUrl, ConfigDict
from pydantic.dataclasses import dataclass
from slack_bolt.context.say.async_say import AsyncSay


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class Job:
    url: AnyHttpUrl
    thread_ts: str
    say: AsyncSay

    @property
    def reply(self):
        return partial(self.say, thread_ts=self.thread_ts)


job_queue: asyncio.Queue[Job] = asyncio.Queue()
