import asyncio
import json
from asyncio import Task, Future
from typing import Optional

from app.store import Store
from app.store.vk_api.dataclasses import Update, UpdateMessage, UpdateCallback


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.game_timeout_tasks = dict()
        self.tasks: list = []
        self.workers = 16

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.app.logger.exception(
                'polling failed', exc_info=future.exception()
            )

    async def process_update(self):
        for i in range(self.workers):
            task = asyncio.create_task(self.worker())
            self.tasks.append(task)

        await asyncio.sleep(3)

        for task in self.tasks:
            task.cancel()
        self.tasks = []

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
            updates = await self.store.vk_api.poll()
            if updates:
                await self.process_update()

    async def worker(self):
        while True:
            message = await self.store.vk_api.app.rabbit.consume()
            update = await self._create_update(json.loads(message.body.decode()))
            await self.store.bots_manager.handle_updates(update)
            await message.ack()

    @staticmethod
    async def _create_update(update: dict) -> Optional[Update]:
        if update['type'] == 'message_new':
            data = update['object']['message']
            return Update(
                type=update['type'],
                object=UpdateMessage(
                    text=data['text'],
                    user_id=data['from_id'],
                    peer_id=data['peer_id'],
                    action=data.get('action'),
                    message_id=data.get("conversation_message_id")
                ))
        elif update['type'] == 'message_event':
            data = update['object']
            return Update(
                type=update['type'],
                object=UpdateCallback(
                    user_id=data['user_id'],
                    peer_id=data['peer_id'],
                    payload=data['payload'],
                    message_id=data.get("conversation_message_id"),
                    event_id=data.get("event_id")
                ))
