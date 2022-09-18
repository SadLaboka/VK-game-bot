import aioredis
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.web.app import Application


class RedisDatabase:
    def __init__(self, app: "Application"):
        self.app = app

        self.answered_questions: Optional[aioredis.Redis] = None
        self.answer_queue: Optional[aioredis.Redis] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self.answered_questions = aioredis.from_url(
            f'redis://{self.app.config.redis.host}'
            f':{self.app.config.redis.port}/0')

        self.answer_queue = aioredis.from_url(
            f'redis://{self.app.config.redis.host}'
            f':{self.app.config.redis.port}/1')

    async def disconnect(self, *_: list, **__: dict) -> None:
        if self.answered_questions:
            await self.answered_questions.close()
        if self.answer_queue:
            await self.answer_queue.close()
