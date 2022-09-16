import asyncio
import json

from typing import TYPE_CHECKING, Optional

from app.smart_peoples.models import Session
from app.store.vk_api.dataclasses import UpdateMessage, Update, UpdateCallback
from app.store.vk_api.enums import CommandKind, SessionStatusKind

if TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, update: Update):
        if update.type == 'message_event':
            await self._callback_handler(update.object)
        elif update.type == 'message_new':
            await self._message_handler(update.object)

    async def _callback_handler(self, callback: UpdateCallback):
        command = callback.payload.get("command")
        if command == CommandKind.JOIN:
            await self._join_the_game(callback)
        elif command == CommandKind.START:
            await self.start_game_session(
                callback.peer_id,
                callback.user_id
            )
        elif command == CommandKind.FINISH:
            messages = []
            messages.append("=================FINISH=================")
            messages.append("Игра завершена!")
            messages.append("======================================")
            message = "%0A %0A".join(messages)
            await self.app.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message=message
            )
            session = await self._get_current_session(callback.peer_id)
            session.status = SessionStatusKind.FINISHED
            await self.app.store.game.update_session(session)
            await self.app.store.bots_manager.send_start_message(callback.peer_id)
        elif command == CommandKind.SHOW_INFO:
            session = await self._get_current_session(callback.peer_id)
            if session.started_by != callback.user_id:
                return
            messages = []
            if session.status == SessionStatusKind.PREPARED:
                messages.append("=================INFO=================")
                messages.append("Игра на стадии подготовки")
                players_statuses = await self.app.store.game.\
                    get_players_statuses(session.id)
                messages.append(f"Количество присоединившихся игроков: {len(players_statuses)}")
                messages.append("======================================")
                message = "%0A %0A".join(messages)
            elif session.status == SessionStatusKind.ACTIVE:
                messages.append("=================INFO=================")
                messages.append("Игра уже идет")
                messages.append("======================================")
                message = "%0A %0A".join(messages)
            else:
                return
            await self.app.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message=message
            )

    async def _message_handler(self, message: UpdateMessage):
        action = message.action
        invite_type = "chat_invite_user"
        if action is not None:
            type_ = action.get("type")
            member = action.get("member_id")
            if type_ == invite_type and member == -self.app.config.bot.group_id:
                peer_id = message.peer_id
                await self.send_start_message(peer_id)
        if message.text.startswith("/duration "):
            time = message.text.split(" ")[-1]
            try:
                time = int(time)
            except Exception:
                return
            session = await self._get_current_session(message.peer_id)
            if session is None:
                return
            elif session.status != SessionStatusKind.PREPARED:
                return
            session.session_duration = time
            await self.app.store.game.update_session(session)
            await self.app.store.vk_api.send_message(
                peer_id=message.peer_id,
                message=f"Время игры было изменено на {time}"
            )
        elif message.text.startswith("/answer_time "):
            time = message.text.split(" ")[-1]
            try:
                time = int(time)
            except Exception:
                return
            session = await self._get_current_session(message.peer_id)
            if session is None:
                return
            elif session.status != SessionStatusKind.PREPARED:
                return
            session.response_time = time
            await self.app.store.game.update_session(session)
            await self.app.store.vk_api.send_message(
                peer_id=message.peer_id,
                message=f"Время на ответ было изменено на {time}"
            )

    async def _join_the_game(self, callback: UpdateCallback):
        session = await self._get_current_session(callback.peer_id)
        if not session.status == SessionStatusKind.PREPARED:
            return
        vk_id = callback.user_id
        user = await self.app.store.vk_api.get_user(vk_id)
        player = await self.app.store.game.get_player_by_vk_id(vk_id)
        if not player:
            player = await self.app.store.game.create_player(
                vk_id, user.first_name, user.last_name)
        player_status = await self.app.store.game.get_player_status(player.id, session.id)
        if player_status:
            await self.app.store.vk_api.send_message_event_answer(
                event_id=callback.event_id,
                user_id=callback.user_id,
                peer_id=callback.peer_id,
                event_data=json.dumps({
                    "type": "show_snackbar",
                    "text": "Вы уже присоединились к игре!"
                })
            )
        else:
            await self.app.store.game.create_player_status(player.id, session.id)
            player.games_count += 1
            await self.app.store.game.update_player(player)

            await self.app.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message=f'@id{callback.user_id} присоединился к игре!'
            )

    async def send_start_message(self, peer_id):
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

    async def start_game_session(self, peer_id: int, started_by: int):
        if await self.check_sessions_in_chat(peer_id):
            session = await self.app.store.game.create_session(
                peer_id, started_by
            )
            message_id = await self._send_game_start_message(peer_id)
            session.start_message_id = message_id
            await self.app.store.game.update_session(session)
            # await self._activate_session(peer_id)

    async def _send_game_start_message(self, peer_id: int):
        message = '=================START=================%0A %0AИгра ' \
                  'начинается! Чтобы присоединиться - нажми на кнопку!'
        join_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": CommandKind.JOIN},
             "label": "Присоединиться"},
            color="positive",
        )
        info_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": CommandKind.SHOW_INFO},
             "label": "Показать информацию"},
            color="primary"
        )
        finish_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": CommandKind.FINISH},
             "label": "Завершить игру"},
            color="negative",
        )

        buttons = [[join_button], ]
        keyboard = await self.app.store.vk_api.build_keyboard(
            buttons,
            {"inline": True}
        )

        data = await self.app.store.vk_api.send_message(
            peer_ids=peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )
        message_id = data["response"][0]["conversation_message_id"]

        messages = []
        messages.append(
            "Игрок, стартовавший игру, может выбрать "
            "длительность игры и время на ответ")
        messages.append("Для этого напишите в чат "
                        "/duration {Время} и /answer_time {Время}")
        messages.append("Чтобы получить информацию о текущем состоянии игры,"
                        " нажмите на кнопку снизу.")
        messages.append(
            "Вы можете завершить игру в любой момент, нажав на кнопку снизу.")
        messages.append("======================================")
        message = "%0A %0A".join(messages)
        buttons = [[info_button], [finish_button]]
        keyboard = await self.app.store.vk_api.build_keyboard(
            buttons=buttons
        )

        await self.app.store.vk_api.send_message(
            peer_id=peer_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )
        return message_id

    async def check_sessions_in_chat(self, peer_id: int) -> bool:
        if await self._get_current_session(peer_id) is not None:
            return False
        return True

    async def _activate_session(self, peer_id: int):
        await asyncio.sleep(30)
        session = await self._get_current_session(peer_id)
        if session.status == SessionStatusKind.PREPARED:
            session.status = SessionStatusKind.ACTIVE
            await self.app.store.game.update_session(session)
            keyboard = await self.app.store.vk_api.build_keyboard([], {"inline": True})
            await self.app.store.vk_api.update_message(
                peer_id=peer_id,
                conversation_message_id=session.start_message_id,
                message="Игра уже началась!",
                keyboard=json.dumps(keyboard)
            )

    async def _get_current_session(
            self, peer_id: int) -> Optional[Session]:
        sessions = await self.app.store.game.get_sessions_by_chat_id(peer_id)
        for session in sessions:
            if (session.status == SessionStatusKind.ACTIVE) \
                    or (session.status == SessionStatusKind.PREPARED):
                return session
        return None
