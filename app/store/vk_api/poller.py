import asyncio
from asyncio import Task, Future
from typing import Optional, List, TYPE_CHECKING

from app.store import Store
from app.store.vk_api.dataclasses import Update


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.primary_queue: Optional[asyncio.Queue] = None
        self.tasks: Optional[list] = []

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.app.logger.exception(
                'polling failed', exc_info=future.exception()
            )

    async def process_update(self, updates: list[Update]):
        for update in updates:
            self.primary_queue.put_nowait(update)
        main_task = asyncio.create_task(self.worker())

        await self.primary_queue.join()
        main_task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def start(self):
        self.primary_queue = asyncio.Queue()
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
            updates = await self.store.vk_api.poll()
            if updates:
                await self.process_update(updates)

    async def worker(self):
        while True:
            update = await self.primary_queue.get()
            await self.store.bots_manager.handle_updates(update)
            self.primary_queue.task_done()
