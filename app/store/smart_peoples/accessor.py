import random
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import select, and_, update
from sqlalchemy.exc import IntegrityError

from app.base.base_accessor import BaseAccessor
from app.smart_peoples.models import Session, SessionModel, PlayerStatus, PlayersStatusModel, Difficulty, \
    DifficultyModel, Player, PlayerModel

if TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):

    async def connect(self, app: "Application"):
        config = self.app.config
        difficulty1 = DifficultyModel(
            id=1,
            title=config.difficulty1.title,
            right_answers_to_win=config.difficulty1.right_answers_to_win,
            wrong_answers_to_lose=config.difficulty1.wrong_answers_to_lose
        )
        difficulty2 = DifficultyModel(
            id=2,
            title=config.difficulty2.title,
            right_answers_to_win=config.difficulty2.right_answers_to_win,
            wrong_answers_to_lose=config.difficulty2.wrong_answers_to_lose
        )
        difficulty3 = DifficultyModel(
            id=3,
            title=config.difficulty3.title,
            right_answers_to_win=config.difficulty3.right_answers_to_win,
            wrong_answers_to_lose=config.difficulty3.wrong_answers_to_lose
        )
        try:
            async with self.app.database.session.begin() as conn:
                conn.add(difficulty1)
                conn.add(difficulty2)
                conn.add(difficulty3)
        except IntegrityError:
            pass

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
                winner_id=session.winner_id
            ))

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
