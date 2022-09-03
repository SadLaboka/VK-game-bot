import asyncio
from asyncio import Task, Future
from typing import Optional

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.app.logger.exception(
                'polling failed', exc_info=future.exception()
            )

    async def start(self):
        task = asyncio.create_task(self.poll())
        task.add_done_callback(self._done_callback)
        self.is_running = True
        self.poll_task = task

    async def stop(self):
        self.is_running = False
        if self.poll_task:
            await asyncio.wait([self.poll_task], timeout=26)
        self.poll_task.cancel()

    async def poll(self):
        while self.is_running:
            await self.store.vk_api.poll()
