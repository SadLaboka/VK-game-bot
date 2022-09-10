import json

from typing import List, TYPE_CHECKING

from app.store.bot.game_session import GameSession
from app.store.vk_api.dataclasses import Update, UpdateMessage, UpdateCallback

if TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            if update.type == 'message_event':
                command = update.object.payload.get("command")
            else:
                command = None
            if update.type == 'message_new':
                await self._message_handler(update.object)

            if command == "start":
                await self._start_game_session(update.object.peer_id)

    async def _message_handler(self, message: UpdateMessage):
        action = message.action
        invite_type = "chat_invite_user"
        type_ = action.get("type")
        member = action.get("member_id")
        if type_ == invite_type and member == -self.app.config.bot.group_id:
            peer_id = message.peer_id
            await self.send_start_message(peer_id)

    async def send_start_message(self, peer_id):
        message = "Я готов к игре!" \
                  " Чтобы начать игру - нажмите на кнопку снизу!"
        start_button = await self.app.store.vk_api.make_button(
            color="primary",
            type="callback",
            payload={"command": "start"},
            label="Начать игру",
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

    async def _start_game_session(self, peer_id: int):
        game_session = GameSession(self.app.store, peer_id)
        await game_session.start()
        await self.app.store.vk_api.add_poller(game_session)
