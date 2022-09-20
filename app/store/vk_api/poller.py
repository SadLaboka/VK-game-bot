import asyncio
from asyncio import Task, Future
from collections import defaultdict
from typing import Optional, List, TYPE_CHECKING, DefaultDict

from app.store import Store
from app.store.vk_api.dataclasses import Update


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.queue: Optional[asyncio.Queue] = None
        self.game_timeout_tasks = dict()
        self.tasks: list = []
        self.workers = 8

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.app.logger.exception(
                'polling failed', exc_info=future.exception()
            )

    async def process_update(self, updates: list[Update]):
        for update in updates:
            self.queue.put_nowait(update)
        for i in range(self.workers):
            task = asyncio.create_task(self.worker())
            self.tasks.append(task)

        await self.queue.join()

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []

    async def start(self):
        self.queue = asyncio.Queue()
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
            update = await self.queue.get()
            await self.store.bots_manager.handle_updates(update)
            self.queue.task_done()
