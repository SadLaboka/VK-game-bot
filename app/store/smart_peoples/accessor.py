import random
from typing import Optional, List, TYPE_CHECKING, Union

from sqlalchemy import select, and_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.smart_peoples.models import Session, SessionModel, PlayerStatus, PlayersStatusModel, Difficulty, \
    DifficultyModel, Player, PlayerModel, PlayerStatusNested

if TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):

    async def create_session(self, chat_id: int, started_by: int) -> Session:
        new_session = SessionModel(
            chat_id=chat_id,
            started_by_vk_id=started_by
        )

        async with self.app.database.session() as conn:
            conn.add(new_session)
            await conn.commit()
            await conn.refresh(new_session)

        return new_session.to_dc()

    async def update_player(
            self,
            player: Player
    ) -> None:
        async with self.app.database.session.begin() as conn:
            await conn.execute(update(PlayerModel).where(
                PlayerModel.id == player.id
            ).values(
                games_count=player.games_count,
                wins_count=player.wins_count,
                loses_count=player.loses_count
            ))

    async def update_player_status(
            self,
            status: Union[PlayerStatus, PlayerStatusNested]
    ) -> None:
        async with self.app.database.session.begin() as conn:
            await conn.execute(update(PlayersStatusModel).where(
                PlayersStatusModel.id == status.id
            ).values(
                right_answers=status.right_answers,
                wrong_answers=status.wrong_answers,
                is_won=status.is_won,
                is_lost=status.is_lost
            ))

    async def get_sessions_by_page(
            self, page: Optional[Union[str, int, None]] = None
    ) -> List[Session]:
        if page:
            page = int(page)
        else:
            page = 1
        limit = 10
        offset = (page - 1) * limit
        async with self.app.database.session.begin() as conn:
            sessions = await conn.scalars(
                select(SessionModel).offset(offset).limit(limit)
            )
        return [s.to_dc() for s in sessions]

    async def update_session(self, session: Session) -> None:
        async with self.app.database.session.begin() as conn:
            await conn.execute(update(SessionModel).where(
                SessionModel.id == session.id
            ).values(
                status=session.status,
                response_time=session.response_time,
                session_duration=session.session_duration,
                start_message_id=session.start_message_id,
                finished_at=session.finished_at,
                winner_id=session.winner_id,
                move_number=session.move_number,
                answering_player_vk_id=session.answering_player_vk_id
            ))

    async def get_players_statuses_by_session_id(
            self, session_id: int) -> List[PlayerStatusNested]:
        async with self.app.database.session.begin() as conn:
            result = await conn.scalars(
                select(PlayersStatusModel).
                where(PlayersStatusModel.session_id == session_id).
                options(joinedload(PlayersStatusModel.player)).
                options(joinedload(PlayersStatusModel.difficulty))
            )

        return [
            player.to_nested_dc() for player in result.unique()
        ] if result else []

    async def create_answered_questions_list(self, session_id: int):
        await self.app.redis.answered_questions.lpush(
            str(session_id), 0, 0)

    async def add_answered_question(
            self, session_id: int, question_id: int) -> None:
        await self.app.redis.answered_questions.lpushx(
            str(session_id), question_id)

    async def get_responder_queue_length(self, session_id: int) -> int:
        queue = await self.app.redis.answer_queue.lrange(str(session_id), 0, -1)
        return len(queue)

    async def create_answer_queue(
            self, session_id: int, statuses: List[PlayerStatusNested]) -> None:
        statuses.sort(key=lambda status: status.difficulty_id)
        answer_queue = [status.player.vk_id for status in statuses]
        await self.app.redis.answer_queue.lpush(str(session_id), *answer_queue)

    async def get_current_responder(self, session_id: int) -> int:
        responder = await self.app.redis.answer_queue.lpop(str(session_id))
        await self.app.redis.answer_queue.rpushx(str(session_id), responder)
        return int(responder)

    async def get_next_responder(self, session_id: int) -> int:
        responder = await self.app.redis.answer_queue.lrange(
            str(session_id), 0, 1)
        return int(responder[0])

    async def get_answered_questions_list(
            self, session_id: int) -> Optional[List[int]]:
        lst = await self.app.redis.answered_questions.lrange(
            str(session_id), 0, -1)
        return [int(id_) for id_ in lst] if lst else None

    async def remove_player_from_queue(self, session_id: int) -> None:
        await self.app.redis.answer_queue.rpop(str(session_id))

    async def remove_answer_queue(self, session_id: int) -> None:
        await self.app.redis.answer_queue.delete(str(session_id))

    async def remove_answered_questions_list(self, session_id: int) -> None:
        await self.app.redis.answered_questions.delete(str(session_id))

    async def get_session_by_id(self, id_: int) -> Optional[Session]:
        async with self.app.database.session.begin() as conn:
            session = (await conn.scalars(
                select(SessionModel).where(SessionModel.id == id_))).first()
        return session.to_dc() if session else None

    async def get_sessions_by_chat_id(
            self, chat_id: int) -> Optional[List[Session]]:
        async with self.app.database.session.begin() as conn:
            sessions = (
                await conn.scalars(
                    select(SessionModel).where(SessionModel.chat_id == chat_id)
                ))
        return [session.to_dc() for session in sessions] if sessions else None

    async def create_player_status(
            self,
            player_id: int,
            session_id: int,
            difficulty_id: Optional[int] = None) -> PlayerStatus:
        if difficulty_id is None:
            difficulty_id = await self.get_random_difficulty()
        new_player_status = PlayersStatusModel(
            player_id=player_id,
            session_id=session_id,
            difficulty_id=difficulty_id.id
        )
        async with self.app.database.session.begin() as conn:
            conn.add(new_player_status)
        return new_player_status.to_dc()

    async def create_player(
            self,
            vk_id: int,
            first_name: str,
            last_name: str) -> Player:
        new_player = PlayerModel(
            vk_id=vk_id,
            first_name=first_name,
            last_name=last_name
        )

        async with self.app.database.session.begin() as conn:
            conn.add(new_player)
        return new_player.to_dc()

    async def get_player_status(
            self,
            player_id: int,
            session_id: int) -> Optional[PlayerStatus]:
        async with self.app.database.session.begin() as conn:
            status = (
                await conn.scalars(
                    select(PlayersStatusModel).where(
                        and_(
                            PlayersStatusModel.player_id == player_id,
                            PlayersStatusModel.session_id == session_id
                        )))).first()
        return status.to_dc() if status else None

    async def get_players_statuses(
            self,
            session_id: int
    ) -> List[PlayerStatus]:
        async with self.app.database.session.begin() as conn:
            statuses = (
                await conn.scalars(
                    select(PlayersStatusModel).where(
                        PlayersStatusModel.session_id == session_id
                    )))
        return [status.to_dc() for status in statuses] if statuses else []

    async def get_player_by_vk_id(self, vk_id: int) -> Optional[Player]:
        async with self.app.database.session.begin() as conn:
            player = (await conn.scalars(
                select(PlayerModel).where(PlayerModel.vk_id == vk_id))).first()
        return player.to_dc() if player else None

    async def get_random_difficulty(self) -> Difficulty:
        async with self.app.database.session.begin() as conn:
            difficulties = (await conn.scalars(select(DifficultyModel))).fetchall()
        return random.choice(difficulties)

    async def get_difficulty_by_id(self, id_: int) -> Optional[Difficulty]:
        async with self.app.database.session.begin() as conn:
            difficulty = (await conn.scalars(
                select(DifficultyModel).where(DifficultyModel.id == id_))).first()
        return difficulty.to_dc() if difficulty else None
