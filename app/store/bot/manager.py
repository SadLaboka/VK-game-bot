import asyncio
import json

from typing import TYPE_CHECKING

from app.store.bot.game_session import GameSession
from app.store.vk_api.dataclasses import Update, UpdateMessage
from app.store.vk_api.enums import CommandKind

if TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, queue: asyncio.Queue):
        update = await queue.get()
        command = None
        handle_result = None
        if update.type == 'message_event':
            command = update.object.payload.get("command")
        elif update.type == 'message_new':
            handle_result = await self._message_handler(update.object)
        if command == CommandKind.start.value:
            handle_result = await self._start_game_session(
                update.object.peer_id)
        if handle_result is None:
            await queue.put(update)

    async def _message_handler(self, message: UpdateMessage):
        action = message.action
        invite_type = "chat_invite_user"
        type_ = action.get("type")
        member = action.get("member_id")
        if type_ == invite_type and member == -self.app.config.bot.group_id:
            peer_id = message.peer_id
            await self.send_start_message(peer_id)
            return True

    async def send_start_message(self, peer_id) -> bool:
        message = "Я готов к игре!" \
                  " Чтобы начать игру - нажмите на кнопку снизу!"
        start_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": "start"},
             "label": "Начать игру"},
            color="primary",
        )
        buttons = [[start_button], ]
        keyboard = await self.app.store.vk_api.build_keyboard(
            buttons=buttons
        )
        await self.app.store.vk_api.send_message(
            peer_id=peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )
        return True

    async def _start_game_session(self, peer_id: int) -> bool:
        game_session = GameSession(self.app.store, peer_id)
        await game_session.start()
        await self.app.store.vk_api.add_poller(game_session)
        return True
