import asyncio
import json
from asyncio import tasks

from app.store import Store
from app.store.vk_api.dataclasses import Update, UpdateCallback
from app.store.vk_api.enums import CommandKind
from app.store.vk_api.poller import Poller


class GameSession(Poller):
    def __init__(
            self, store: Store, peer_id: int):
        super().__init__(store)
        self.peer_id = peer_id

    async def _handle_updates(self, queue: asyncio.Queue):
        update = await queue.get()
        handle_result = None
        if not update.object.peer_id == self.peer_id:
            await queue.put(update)
            return
        if update.type == "message_event":
            callback = update.object
            handle_result = await self._callback_handler(callback)
        if handle_result is None:
            await queue.put(update)

    async def _callback_handler(self, callback: UpdateCallback) -> bool:
        command = callback.payload.get("command")
        if command == CommandKind.join.value:
            return await self._join_the_game(callback)
        elif command == CommandKind.finish.value:
            await self.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message="Игра завершена!",
            )
            await self.store.bots_manager.send_start_message(self.peer_id)
            await self.store.vk_api.remove_poller(self)
            await self.stop()
            return True

    async def check_sessions_in_chat(self) -> bool:
        return False

    async def _join_the_game(self, callback: UpdateCallback) -> bool:
        keyboard = await self.store.vk_api.build_keyboard(
            [],
            {"inline": True}
        )
        await self.store.vk_api.send_message(
            peer_id=callback.peer_id,
            message=f'@id{callback.user_id} присоединился к игре!',
            keyboard=json.dumps(keyboard)
        )
        return True

    async def _send_game_start_message(self):
        message = 'Игра начинается! Чтобы присоединиться - нажми на кнопку!'
        join_button = await self.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": "join"},
             "label": "Присоединиться"},
            color="positive",
        )
        finish_button = await self.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": "finish"},
             "label": "Завершить игру"},
            color="negative",
        )

        buttons = [[join_button], ]
        keyboard = await self.store.vk_api.build_keyboard(
            buttons,
            {"inline": True}
        )

        await self.store.vk_api.send_message(
            peer_id=self.peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )

        message = "Вы можете завершить игру в " \
                  "любой момент, нажав на кнопку снизу."
        buttons = [[finish_button], ]
        keyboard = await self.store.vk_api.build_keyboard(
            buttons=buttons
        )

        await self.store.vk_api.send_message(
            peer_id=self.peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )

    async def start(self):
        if not await self.check_sessions_in_chat():
            task = tasks.create_task(self.poll())
            self.is_running = True
            self.poll_task = task
            await self._send_game_start_message()

    async def poll(self):
        while self.is_running:
            await self.store.vk_api.poll()
            await self._handle_updates(self.store.vk_api.queue)
