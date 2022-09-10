import json
from asyncio import tasks

from app.store import Store
from app.store.vk_api.dataclasses import Update, UpdateCallback
from app.store.vk_api.poller import Poller


class GameSession(Poller):
    def __init__(
            self, store: Store, peer_id: int):
        super().__init__(store)
        self.peer_id = peer_id

    async def _handle_updates(self, updates: list[Update]):
        for update in updates:
            if not update.object.peer_id == self.peer_id:
                continue
            if update.type == "message_event":
                callback = update.object
                await self._callback_handler(callback)

    async def _callback_handler(self, callback: UpdateCallback):
        command = callback.payload.get("command")
        if command == "join":
            await self._join_the_game(callback)
        elif command == "finish":
            await self.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message="Игра завершена!",
            )
            await self.store.bots_manager.send_start_message(self.peer_id)
            await self.store.vk_api.remove_poller(self)
            await self.stop()

    async def check_sessions_in_chat(self) -> bool:
        return False

    async def _join_the_game(self, callback: UpdateCallback) -> None:
        message = f'@id{callback.user_id} присоединился к игре!'
        keyboard = await self.store.vk_api.build_keyboard(
            inline=True,
            buttons=[]
        )
        peer_id = callback.peer_id
        await self.store.vk_api.send_message(
            peer_id=peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )

    async def _send_game_start_message(self):
        message = 'Игра начинается! Чтобы присоединиться - нажми на кнопку!'
        join_button = await self.store.vk_api.make_button(
            color="positive",
            type="callback",
            payload={"command": "join"},
            label="Присоединиться",
        )
        finish_button = await self.store.vk_api.make_button(
            color="negative",
            type="callback",
            payload={"command": "finish"},
            label="Завершить игру",
        )

        buttons = [[join_button], ]
        keyboard = await self.store.vk_api.build_keyboard(
            buttons=buttons,
            inline=True
        )

        await self.store.vk_api.send_message(
            peer_id=self.peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )

        message = "Вы можете завершить игру в любой момент, нажав на кнопку снизу."
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
            updates = await self.store.vk_api.poll()
            print(updates)
            await self._handle_updates(updates)
