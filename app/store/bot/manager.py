import asyncio
import datetime
import json
import random

from typing import TYPE_CHECKING, Optional, List

from app.smart_peoples.models import Session, PlayerStatusNested
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
            session = await self._get_current_session(callback.peer_id)
            text = []
            text.append(f"Игра завершена игроком @id{callback.user_id}!")
            if session.status == SessionStatusKind.ACTIVE:
                count_current_players = await self.app.store.game\
                    .get_responder_queue_length(session.id)
                statuses = await self.app.store.game\
                    .get_players_statuses_by_session_id(session.id)
                statuses.sort(
                    key=lambda status_: status_.right_answers, reverse=True)
                text.append(f"Количество оставшихся игроков:"
                            f" {count_current_players}")
                text.append("Оставшиеся игроки:")
                lost_players = []
                info_lst = await self._build_info_list(statuses)
                text.extend(info_lst)
                for status in statuses:
                    if status.is_lost:
                        lost_players.append(status)
                if lost_players:
                    text.append(f"Количество проигравших игроков:"
                                f" {len(lost_players)}")
                    text.append("Проигравшие игроки:")
                    info_lst_lost = await self._build_info_list(lost_players)
                    text.extend(info_lst_lost)
            message = await self._build_messages_block(text, "FINISH")
            await self.app.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message=message
            )
            await self._finish_the_game(callback.peer_id, "Interrupted")
            await asyncio.sleep(0.3)
            await self.app.store.bots_manager.send_start_message(
                callback.peer_id)
        elif command == CommandKind.SHOW_INFO:
            session = await self._get_current_session(callback.peer_id)
            if session.started_by != callback.user_id:
                return
            text = []
            if session.status == SessionStatusKind.PREPARED:
                text.append("Игра на стадии подготовки")
                players_statuses = await self.app.store.game. \
                    get_players_statuses_by_session_id(session.id)
                text.append(f"Количество присоединившихся игроков: "
                            f"{len(players_statuses)}")
                if players_statuses:
                    text.append("Игроки:")
                    for status in players_statuses:
                        text.append(f" -> @id{status.player.vk_id}"
                                    f" {status.player.first_name}"
                                    f" {status.player.last_name}"
                                    f"%0A-----Уровень сложности: "
                                    f"{status.difficulty.title}")
                message = await self._build_messages_block(text, "=INFO=")
            elif session.status == SessionStatusKind.ACTIVE:
                text.append("Игра уже идет!")
                count_current_players = await self.app.store.game \
                    .get_responder_queue_length(session.id)
                players_statuses = await self.app.store.game. \
                    get_players_statuses_by_session_id(session.id)
                text.append(f"Количество оставшихся игроков:"
                            f" {count_current_players}")
                text.append("Активные игроки:")
                lost_players = []
                info_lst = await self._build_info_list(players_statuses)
                text.extend(info_lst)
                for status in players_statuses:
                    if status.is_lost:
                        lost_players.append(status)
                if lost_players:
                    text.append(f"Количество проигравших игроков:"
                                f" {len(lost_players)}")
                    text.append("Проигравшие игроки:")
                    info_lst_lost = await self._build_info_list(lost_players)
                    text.extend(info_lst_lost)

                message = await self._build_messages_block(text, "=INFO=")
            else:
                return
            await self.app.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message=message
            )
        elif command == CommandKind.ANSWER:
            session = await self._get_current_session(callback.peer_id)
            if session is None or session \
                    .move_number != callback.payload.get("move_number"):
                await self.app.store.vk_api.send_message_event_answer(
                    event_id=callback.event_id,
                    user_id=callback.user_id,
                    peer_id=callback.peer_id,
                    event_data=json.dumps({
                        "type": "show_snackbar",
                        "text": "Кнопка устарела!"
                    })
                )
                return
            if session.answering_player_vk_id != callback.user_id:
                await self.app.store.vk_api.send_message_event_answer(
                    event_id=callback.event_id,
                    user_id=callback.user_id,
                    peer_id=callback.peer_id,
                    event_data=json.dumps({
                        "type": "show_snackbar",
                        "text": "Сейчас не ваша очередь!"
                    })
                )
            else:
                is_correct = callback.payload.get("is_correct")
                answer_title = callback.payload.get("answer_title")
                question_title = callback.payload.get("question_title")
                keyboard = await self.app.store.vk_api.build_keyboard(
                    [], {"inline": True})
                await self.app.store.vk_api.update_message(
                    peer_id=callback.peer_id,
                    conversation_message_id=callback.message_id,
                    message=f"Вопрос: {question_title}",
                    keyboard=json.dumps(keyboard)
                )
                player = await self.app.store.game.get_player_by_vk_id(
                    callback.user_id)
                status = await self.app.store.game.get_player_status(
                    player.id, session.id)
                difficulty = await self.app.store.game.get_difficulty_by_id(
                    status.difficulty_id)
                text = []
                text.append(f"Игрок выбрал ответ \"{answer_title}\"")
                if is_correct:
                    text.append("Это правильный ответ!")
                    status.right_answers += 1
                    if status.right_answers == difficulty.right_answers_to_win:
                        status.is_won = True
                        text.append(f"Игрок @id{player.vk_id} "
                                    f"{player.first_name}"
                                    f" {player.last_name}"
                                    f" одерживает победу!")
                        await self._finish_the_game(
                            callback.peer_id, "Finished", player.id)
                else:
                    text.append("Это неправильный ответ!")
                    status.wrong_answers += 1
                    if status.wrong_answers == difficulty \
                            .wrong_answers_to_lose:
                        status.is_lost = True
                        text.append(f"К сожалению, игрок "
                                    f"@id{player.vk_id} "
                                    f"{player.first_name}"
                                    f" {player.last_name}"
                                    f" выбывает!")
                        await self.app.store.game.remove_player_from_queue(
                            session.id)
                await self.app.store.game.update_player_status(status)
                message = "%0A %0A".join(text)
                await asyncio.sleep(0.5)
                await self.app.store.vk_api.send_message(
                    peer_id=callback.peer_id,
                    message=message
                )
                await asyncio.sleep(0.5)
                responders_queue_length = await self.app.store.game \
                    .get_responder_queue_length(session.id)
                if status.is_won:
                    statuses = await self.app.store.game \
                        .get_players_statuses_by_session_id(session.id)
                    for player_status in statuses:
                        if player_status.id != status.id:
                            player_status.player.loses_count += 1
                            player_status.is_lost = True
                            await self.app.store.game.update_player(
                                player_status.player
                            )
                            await self.app.store.game.update_player_status(
                                player_status)
                    text = []
                    text.append(f"Игра завершена победой игрока "
                                f"@id{callback.user_id}!")
                    updated_statuses = await self.app.store.game \
                        .get_players_statuses_by_session_id(session.id)
                    updated_statuses.sort(
                        key=lambda status_: status_.right_answers, reverse=True)
                    text.append("Проигравшие игроки:")
                    lost_players = []
                    for player_status in updated_statuses:
                        if not player_status.is_won:
                            lost_players.append(player_status)
                    if lost_players:
                        info_lst = await self._build_info_list(lost_players)
                        text.extend(info_lst)
                    message = await self._build_messages_block(text, "FINISH")
                    await self.app.store.vk_api.send_message(
                        peer_id=callback.peer_id,
                        message=message
                    )
                    await asyncio.sleep(0.3)
                    await self.send_start_message(callback.peer_id)
                    player.wins_count += 1
                    await self.app.store.game.update_player(player)
                elif responders_queue_length <= 1:
                    winner_vk_id = await self.app.store.game \
                        .get_next_responder(session.id)
                    winner = await self.app.store.game.get_player_by_vk_id(
                        winner_vk_id)
                    status = await self.app.store.game.get_player_status(
                        winner.id, session.id)
                    status.is_won = True
                    winner.wins_count += 1
                    await self.app.store.game.update_player_status(status)
                    await self.app.store.game.update_player(winner)
                    statuses = await self.app.store.game \
                        .get_players_statuses_by_session_id(session.id)
                    for player_status in statuses:
                        if player_status.id != status.id:
                            player_status.player.loses_count += 1
                            await self.app.store.game.update_player(
                                player_status.player
                            )
                            await self.app.store.game.update_player_status(
                                player_status)
                    text = []
                    text.append("Остался только 1 игрок!")
                    text.append(f"Игра завершена победой игрока "
                                f"@id{winner.vk_id}!")
                    updated_statuses = await self.app.store.game \
                        .get_players_statuses_by_session_id(session.id)
                    updated_statuses.sort(
                        key=lambda status_: status_.right_answers, reverse=True)
                    text.append("Проигравшие игроки:")
                    lost_players = []
                    for player_status in updated_statuses:
                        if not player_status.is_won:
                            lost_players.append(player_status)
                    if lost_players:
                        info_lst = await self._build_info_list(lost_players)
                        text.extend(info_lst)
                    message = await self._build_messages_block(text, "FINISH")
                    await self.app.store.vk_api.send_message(
                        peer_id=callback.peer_id,
                        message=message
                    )
                    await self._finish_the_game(
                        callback.peer_id, "Finished", winner.id)
                    await asyncio.sleep(0.3)
                    await self.send_start_message(callback.peer_id)
                else:
                    await self._next_question(session)

        elif command == CommandKind.CHOICE:
            session = await self._get_current_session(callback.peer_id)
            if session is None or session.move_number != callback.payload.get("move_number"):
                await self.app.store.vk_api.send_message_event_answer(
                    event_id=callback.event_id,
                    user_id=callback.user_id,
                    peer_id=callback.peer_id,
                    event_data=json.dumps({
                        "type": "show_snackbar",
                        "text": "Кнопка устарела!"
                    })
                )
                return
            if session.answering_player_vk_id != callback.user_id:
                await self.app.store.vk_api.send_message_event_answer(
                    event_id=callback.event_id,
                    user_id=callback.user_id,
                    peer_id=callback.peer_id,
                    event_data=json.dumps({
                        "type": "show_snackbar",
                        "text": "Сейчас не ваша очередь!"
                    })
                )
            elif session.question_asked:
                await self.app.store.vk_api.send_message_event_answer(
                    event_id=callback.event_id,
                    user_id=callback.user_id,
                    peer_id=callback.peer_id,
                    event_data=json.dumps({
                        "type": "show_snackbar",
                        "text": "Тема уже выбрана!"
                    })
                )
            else:
                theme_id = callback.payload.get("theme_id")
                theme_title = callback.payload.get("title")
                keyboard = await self.app.store.vk_api.build_keyboard(
                    [], {"inline": True})
                await self.app.store.vk_api.update_message(
                    peer_id=callback.peer_id,
                    conversation_message_id=callback.message_id,
                    message=f"Выбрана тема \"{theme_title}\"!",
                    keyboard=json.dumps(keyboard)
                )
                await self._ask_a_question(session, theme_id)

    async def _build_info_list(self, statuses: List[PlayerStatusNested]) -> List[str]:
        text_lst = []
        for status in statuses:
            text_lst.append(
                f" -> @id{status.player.vk_id} "
                f"{status.player.first_name}"
                f" {status.player.last_name}"
                f"%0A-----Уровень сложности:"
                f" {status.difficulty.title}"
                f"%0A-----Правильных ответов:"
                f" {status.right_answers}"
                f"/{status.difficulty.right_answers_to_win}"
                f"%0A-----Неправильных ответов:"
                f" {status.wrong_answers}"
                f"/{status.difficulty.wrong_answers_to_lose}")
        return text_lst

    async def _build_messages_block(
            self,
            text: List[str],
            head: Optional[str] = None,
            foot: bool = True
    ) -> str:
        if not head:
            head = "======"
        lines = [f"================={head}================="]
        lines.extend(text)
        if foot:
            lines.append("======================================")

        message = "%0A %0A".join(lines)
        return message

    async def _next_question(self, session: Session):
        current_responder = await self.app.store.game.get_current_responder(
            session.id)
        session.answering_player_vk_id = current_responder
        session.move_number += 1
        session.question_asked = False
        await self.app.store.game.update_session(session)
        text = []
        text.append("Продолжаем игру!")
        answering_player = await self.app.store.game.get_player_by_vk_id(
            current_responder)
        text.append(f"Дальше отвечает игрок @id{current_responder}"
                    f" {answering_player.first_name}"
                    f" {answering_player.last_name}")
        message = await self._build_messages_block(text, foot=False)
        await self.app.store.vk_api.send_message(
            peer_id=session.chat_id,
            message=message
        )
        await self._choose_a_question_theme(session)

    async def _message_handler(self, message: UpdateMessage):
        action = message.action
        invite_type = "chat_invite_user"
        if action is not None:
            type_ = action.get("type")
            member = action.get("member_id")
            if type_ == invite_type and member == -self.app.config.bot \
                    .group_id:
                peer_id = message.peer_id
                await self.send_start_message(peer_id)
        session = await self._get_current_session(message.peer_id)
        if session is None:
            return
        elif session.status != SessionStatusKind.PREPARED:
            return
        if message.text.startswith("/duration "):
            time = message.text.split(" ")[-1]
            try:
                time = int(time)
            except Exception:
                return
            if session.started_by != message.user_id:
                return
            if time < 120 or time > 3600:
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
            except TypeError:
                return
            except ValueError:
                return
            if session.started_by != message.user_id:
                return
            if time < 10 or time > 60:
                return
            session.response_time = time
            await self.app.store.game.update_session(session)
            await self.app.store.vk_api.send_message(
                peer_id=message.peer_id,
                message=f"Время на ответ было изменено на {time}"
            )
        elif message.text == "/begin":
            if session.started_by != message.user_id:
                return
            await self.change_game_status_to_active(message.peer_id, session.id)

    async def _join_the_game(self, callback: UpdateCallback):
        session = await self._get_current_session(callback.peer_id)
        if session.move_number != 0 or session.id != callback.payload.get(
                "session"):
            await self.app.store.vk_api.send_message_event_answer(
                event_id=callback.event_id,
                user_id=callback.user_id,
                peer_id=callback.peer_id,
                event_data=json.dumps({
                    "type": "show_snackbar",
                    "text": "Кнопка устарела"
                }))
            return
        if not session.status == SessionStatusKind.PREPARED:
            return
        vk_id = callback.user_id
        user = await self.app.store.vk_api.get_user(vk_id)
        player = await self.app.store.game.get_player_by_vk_id(vk_id)
        if not player:
            player = await self.app.store.game.create_player(
                vk_id, user.first_name, user.last_name)
        player_status = await self.app.store.game.get_player_status(
            player.id, session.id)
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
            player_status = await self.app.store.game.create_player_status(
                player.id, session.id)
            player.games_count += 1
            await self.app.store.game.update_player(player)
            difficulty = await self.app.store.game.get_difficulty_by_id(
                player_status.difficulty_id)
            message = f'@id{callback.user_id} {player.first_name}' \
                      f' {player.last_name} присоединился к игре!' \
                      f'%0A Цвет дорожки: {difficulty.title}'
            await self.app.store.vk_api.send_message(
                peer_id=callback.peer_id,
                message=message
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

    async def _ask_a_question(self, session: Session, theme_id: int) -> bool:
        answered_questions = await self.app.store.game \
            .get_answered_questions_list(session.id)
        player = await self.app.store.game.get_player_by_vk_id(
            session.answering_player_vk_id)
        status = await self.app.store.game.get_player_status(
            player.id, session.id)
        questions = await self.app.store.quizzes.list_questions(
            theme_id, status.difficulty_id, answered_questions)
        if not questions:
            await self._finish_the_game(session.chat_id, "Interrupted")
            text = []
            text.append(f"Игра была завершена, потому что для игрока "
                        f"@id{session.answering_player_vk_id}"
                        f" {player.first_name} {player.last_name} "
                        f"закончились подходящие вопросы!")
            updated_statuses = await self.app.store.game \
                .get_players_statuses_by_session_id(session.id)
            updated_statuses.sort(
                key=lambda status_: status_.right_answers, reverse=True)
            text.append("Оставшиеся игроки:")
            lost_players = []
            info_lst = await self._build_info_list(updated_statuses)
            text.extend(info_lst)
            for status in updated_statuses:
                if status.is_lost:
                    lost_players.append(status)
            if lost_players:
                text.append(f"Количество проигравших игроков:"
                            f" {len(lost_players)}")
                text.append("Проигравшие игроки:")
                info_lst_lost = await self._build_info_list(lost_players)
                text.extend(info_lst_lost)
            message = await self._build_messages_block(text, "FINISH")
            await self.app.store.vk_api.send_message(
                peer_id=session.chat_id,
                message=message
            )
            await self.app.store.bots_manager.send_start_message(
                session.chat_id)
            return False

        question = random.choice(questions)
        await self.app.store.game.add_answered_question(
            session.id, question.id)
        random.shuffle(question.answers)
        buttons = []
        for answer in question.answers:
            button = await self.app.store.vk_api.make_button(
                {"type": "callback",
                 "payload": {"command": "answer",
                             "is_correct": answer.is_correct,
                             "answer_title": answer.title,
                             "question_title": question.title,
                             "move_number": session.move_number},
                 "label": answer.title},
                color="positive",
            )
            buttons.append([button])
        keyboard = await self.app.store.vk_api.build_keyboard(
            buttons, {"inline": True})
        await asyncio.sleep(0.3)
        response = await self.app.store.vk_api.send_message(
            peer_ids=session.chat_id,
            message=f"Вопрос: {question.title}",
            keyboard=json.dumps(keyboard)
        )
        session.question_asked = True
        await self.app.store.game.update_session(session)
        message_id = response["response"][0]["conversation_message_id"]
        await self.next_answer_after_timeout(
            session.chat_id,
            session.id,
            session.response_time,
            session.move_number,
            message_id,
            question.title
        )

    async def start_game_session(self, peer_id: int, started_by: int):
        if await self.check_sessions_in_chat(peer_id):
            session = await self.app.store.game.create_session(
                peer_id, started_by
            )
            message_id = await self._send_game_start_message(peer_id)
            session.start_message_id = message_id
            await self.app.store.game.update_session(session)
            await self.activate_session_after_timeout(peer_id, session.id)

    async def _send_game_start_message(self, peer_id: int):
        session = await self._get_current_session(peer_id)
        text = []
        text.append(f'Новая игра была инициирована игроком'
                    f' @id{session.started_by}')
        text.append('Игра начинается'
                    '! Чтобы присоединиться - нажми на кнопку!')
        text.append("Набор игроков продлится 30 секунд!")
        text.append("Игрок, стартовавший игру, может начать её досрочно."
                    " Для этого напишите в чат /begin")
        text.append(
            "Игрок, стартовавший игру, может выбрать "
            "длительность игры и время на ответ")
        text.append("Для этого напишите в чат "
                    "/duration {Время} и /answer_time {Время}")
        text.append("Чтобы получить информацию о текущем состоянии игры,"
                    " нажмите на кнопку \"Показать информацию\".")
        text.append(
            "Вы можете завершить игру в любой момент,"
            " нажав на кнопку \"Завершить игру\".")
        message = await self._build_messages_block(text, "START=", False)
        join_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": "join",
                         "session": session.id},
             "label": "Присоединиться"},
            color="positive",
        )
        info_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": "show_info"},
             "label": "Показать информацию"},
            color="primary"
        )
        finish_button = await self.app.store.vk_api.make_button(
            {"type": "callback",
             "payload": {"command": "finish"},
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

        buttons = [[info_button], [finish_button]]
        keyboard = await self.app.store.vk_api.build_keyboard(
            buttons=buttons
        )
        await asyncio.sleep(0.3)
        await self.app.store.vk_api.send_message(
            peer_id=peer_id,
            message="======================================",
            keyboard=json.dumps(keyboard)
        )
        return message_id

    async def check_sessions_in_chat(self, peer_id: int) -> bool:
        if await self._get_current_session(peer_id) is not None:
            return False
        return True

    def create_a_prep_timer(self, task):
        async def check_game(task):
            peer_id = task.result()["peer_id"]
            session_id = task.result()["session_id"]
            await self.change_game_status_to_active(peer_id, session_id)

        asyncio.create_task(coro=check_game(task))

    def create_a_session_timer(self, task):
        async def check_game(task):
            session_id = task.result()["session_id"]
            session = await self.app.store.game.get_session_by_id(session_id)
            if session.status == SessionStatusKind.ACTIVE:
                await self._finish_the_game(session.chat_id, "Finished")
                text = []
                text.append(f"Игра завершена по истечению времени!")
                message = await self._build_messages_block(text, "FINISH")
                await self.app.store.vk_api.send_message(
                    peer_id=session.chat_id,
                    message=message
                )
                await self.app.store.bots_manager.send_start_message(
                    session.chat_id)

        asyncio.create_task(coro=check_game(task))

    def create_a_answer_timer(self, task):
        async def check_game(task):
            session_id = task.result()["session_id"]
            move_number = task.result()["move_number"]
            message_id = task.result()["message_id"]
            question_title = task.result()["question_title"]
            session = await self.app.store.game.get_session_by_id(session_id)
            if session.status == SessionStatusKind.ACTIVE and session. \
                    move_number == move_number:
                player = await self.app.store.game.get_player_by_vk_id(
                    session.answering_player_vk_id)
                status = await self.app.store.game.get_player_status(
                    player.id, session.id)
                difficulty = await self.app.store.game.get_difficulty_by_id(
                    status.difficulty_id)
                keyboard = await self.app.store.vk_api.build_keyboard(
                    [], {"inline": True})
                await self.app.store.vk_api.update_message(
                    peer_id=session.chat_id,
                    conversation_message_id=message_id,
                    message=f"Вопрос: {question_title}",
                    keyboard=json.dumps(keyboard)
                )
                text = []
                text.append("Время на ответ кончилось!")
                text.append("Игроку засчитан неправильный ответ!")
                status.wrong_answers += 1
                if status.wrong_answers == difficulty.wrong_answers_to_lose:
                    status.is_lost = True
                    text.append(f"К сожалению, игрок "
                                f"@id{player.vk_id} "
                                f"{player.first_name}"
                                f" {player.last_name}"
                                f" выбывает!")
                    await self.app.store.game.remove_player_from_queue(
                        session.id)
                await self.app.store.game.update_player_status(status)
                message = "%0A %0A".join(text)
                await self.app.store.vk_api.send_message(
                    peer_id=session.chat_id,
                    message=message
                )
                responders_queue_length = await self.app.store.game \
                    .get_responder_queue_length(session.id)
                if responders_queue_length <= 1:
                    winner_vk_id = await self.app.store.game \
                        .get_next_responder(session.id)
                    winner = await self.app.store.game.get_player_by_vk_id(
                        winner_vk_id)
                    status = await self.app.store.game.get_player_status(
                        winner.id, session.id)
                    status.is_won = True
                    winner.wins_count += 1
                    await self.app.store.game.update_player_status(status)
                    await self.app.store.game.update_player(winner)
                    text = []
                    text.append("Остался только 1 игрок!")
                    text.append(f"Игра завершена победой игрока "
                                f"@id{winner.vk_id}!")
                    message = await self._build_messages_block(text, "FINISH")
                    await self.app.store.vk_api.send_message(
                        peer_id=session.chat_id,
                        message=message
                    )
                    await self._finish_the_game(
                        session.chat_id, "Finished", winner.id)
                    await self.send_start_message(session.chat_id)
                    statuses = await self.app.store.game \
                        .get_players_statuses_by_session_id(session.id)
                    for player_status in statuses:
                        if player_status.id != status.id:
                            player_status.player.loses_count += 1
                            await self.app.store.game.update_player(
                                player_status.player
                            )
                            await self.app.store.game.update_player_status(
                                player_status)
                else:
                    await self._next_question(session)

        asyncio.create_task(coro=check_game(task))

    async def activate_session_after_timeout(
            self, peer_id: int, session_id: int):
        task = asyncio.create_task(self.delay_coroutine(30, peer_id, session_id))
        task.add_done_callback(self.create_a_prep_timer)
        session_timeout_tasks = self.app.store.vk_api.poller \
            .game_timeout_tasks.setdefault(session_id, [])
        session_timeout_tasks.append(task)

    async def finish_session_after_timeout(self, peer_id: int, session_id: int):
        session = await self.app.store.game.get_session_by_id(session_id)
        task = asyncio.create_task(self.delay_coroutine(
            session.session_duration, peer_id, session.id))
        task.add_done_callback(self.create_a_session_timer)
        session_timeout_tasks = self.app.store.vk_api.poller \
            .game_timeout_tasks.setdefault(session_id, [])
        session_timeout_tasks.append(task)

    async def next_answer_after_timeout(
            self,
            peer_id: int,
            session_id: int,
            response_time: int,
            move_number: int,
            message_id: int,
            question_title: str
    ):
        task = asyncio.create_task(self.delay_coroutine(
            response_time,
            peer_id,
            session_id,
            move_number,
            message_id,
            question_title
        ))
        task.add_done_callback(self.create_a_answer_timer)
        session_timeout_tasks = self.app.store.vk_api.poller \
            .game_timeout_tasks.setdefault(session_id, [])
        session_timeout_tasks.append(task)

    async def delay_coroutine(
            self,
            delay: int,
            peer_id: int,
            session_id: int,
            move_number: Optional[int] = None,
            message_id: Optional[int] = None,
            question_title: Optional[str] = None
    ):
        result = {"peer_id": peer_id,
                  "session_id": session_id}
        if move_number:
            result["move_number"] = move_number
        if message_id:
            result["message_id"] = message_id
        if question_title:
            result["question_title"] = question_title
        return await asyncio.sleep(delay=delay,
                                   result=result)

    async def change_game_status_to_active(
            self, peer_id: int, session_id: int):
        session = await self.app.store.game.get_session_by_id(session_id)
        if session.status == SessionStatusKind.PREPARED:
            session.status = "Active"
            keyboard = await self.app.store.vk_api.build_keyboard(
                [], {"inline": True})
            text = []
            text.append("Игра уже началась!")
            text.append("Чтобы получить информацию о текущем состоянии игры,"
                        " нажмите на кнопку \"Показать информацию\".")
            text.append("Вы можете завершить игру в любой момент,"
                        " нажав на кнопку \"Завершить игру\".")
            message = await self._build_messages_block(text, "START=", False)
            await self.app.store.vk_api.update_message(
                peer_id=peer_id,
                conversation_message_id=session.start_message_id,
                message=message,
                keyboard=json.dumps(keyboard)
            )
            is_began = await self._begin_the_game(session)
            if not is_began:
                return
            await self.finish_session_after_timeout(
                session.chat_id, session.id)

    async def _begin_the_game(self, session: Session) -> bool:
        players_statuses = await self.app.store.game \
            .get_players_statuses_by_session_id(session.id)
        if not players_statuses:
            await self._finish_the_game(session.chat_id, "Interrupted")
            text = []
            text.append(f"Игра была завершена,"
                        f" потому что ни один игрок не присоединился!")
            message = await self._build_messages_block(text, "FINISH")
            await self.app.store.vk_api.send_message(
                peer_id=session.chat_id,
                message=message
            )
            await self.app.store.bots_manager.send_start_message(
                session.chat_id)
            return False
        elif len(players_statuses) == 1:
            await self._finish_the_game(session.chat_id, "Interrupted")
            text = []
            text.append(f"Игра была завершена,"
                        f" потому что присоединился только 1 человек!")
            message = await self._build_messages_block(text, "FINISH")
            await self.app.store.vk_api.send_message(
                peer_id=session.chat_id,
                message=message
            )
            await self.app.store.bots_manager.send_start_message(
                session.chat_id)
            return False
        await self.app.store.game.create_answer_queue(
            session.id, players_statuses)
        await self.app.store.game.create_answered_questions_list(session.id)
        answering_vk_id = await self.app.store.game.get_current_responder(
            session.id)
        session.answering_player_vk_id = answering_vk_id
        session.move_number += 1
        await self.app.store.game.update_session(session)
        text = []
        text.append("Игра началась!")
        answering_player = await self.app.store.game.get_player_by_vk_id(
            answering_vk_id)
        text.append(f"Первым отвечает игрок @id{answering_vk_id}"
                    f" {answering_player.first_name}"
                    f" {answering_player.last_name}")
        message = await self._build_messages_block(text, "=GAME=", False)
        await asyncio.sleep(0.5)
        await self.app.store.vk_api.send_message(
            peer_id=session.chat_id,
            message=message
        )
        await self._choose_a_question_theme(session)
        return True

    async def _choose_a_question_theme(self, session: Session):
        themes = await self.app.store.quizzes.list_themes()
        random.shuffle(themes)
        buttons = []
        for theme in themes[:3]:
            button = await self.app.store.vk_api.make_button(
                {"type": "callback",
                 "payload": {"command": "choice",
                             "theme_id": theme.id,
                             "title": theme.title,
                             "move_number": session.move_number},
                 "label": theme.title},
                color="primary",
            )
            buttons.append([button])
        keyboard = await self.app.store.vk_api.build_keyboard(
            buttons, {"inline": True})
        await self.app.store.vk_api.send_message(
            peer_id=session.chat_id,
            message="Выбирайте тему вопроса!",
            keyboard=json.dumps(keyboard)
        )

    async def _finish_the_game(self,
                               peer_id: int,
                               status: str,
                               winner_id: Optional[int] = None
                               ):
        session = await self._get_current_session(peer_id)
        session.status = status
        session.finished_at = datetime.datetime.now()
        if winner_id is not None:
            session.winner_id = winner_id
        await self.app.store.game.update_session(session)
        await self.app.store.game.remove_answer_queue(session.id)
        await self.app.store.game.remove_answered_questions_list(session.id)
        keyboard = await self.app.store.vk_api.build_keyboard(
            [], {"inline": True})
        message = await self._build_messages_block(
            ["Игра уже завершена!"], "START=", False)
        await self.app.store.vk_api.update_message(
            peer_id=peer_id,
            conversation_message_id=session.start_message_id,
            message=message,
            keyboard=json.dumps(keyboard)
        )
        session_timeout_tasks = self.app.store.vk_api.poller\
            .game_timeout_tasks.setdefault(session.id, [])
        if session_timeout_tasks:
            for task in session_timeout_tasks:
                task.cancel()
            self.app.store.vk_api.poller.game_timeout_tasks.pop(session.id)

    async def _get_current_session(
            self, peer_id: int) -> Optional[Session]:
        sessions = await self.app.store.game.get_sessions_by_chat_id(peer_id)
        for session in sessions:
            if (session.status == SessionStatusKind.ACTIVE) \
                    or (session.status == SessionStatusKind.PREPARED):
                return session
        return None
