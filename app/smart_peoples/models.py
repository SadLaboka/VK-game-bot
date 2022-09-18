from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Session:
    id: int
    chat_id: int
    started_by: int
    status: str
    response_time: int
    session_duration: int
    started_at: datetime
    move_number: int
    start_message_id: Optional[int] = None
    finished_at: Optional[datetime] = None
    winner_id: Optional[int] = None
    answering_player_vk_id: Optional[int] = None


@dataclass
class PlayerStatus:
    id: int
    player_id: int
    session_id: int
    difficulty_id: int
    right_answers: int
    wrong_answers: int
    is_won: bool
    is_lost: bool


@dataclass
class Player:
    id: int
    vk_id: int
    first_name: str
    last_name: str
    games_count: int
    wins_count: int
    loses_count: int


@dataclass
class PlayerStatusNested(PlayerStatus):
    player: Player


@dataclass
class Difficulty:
    id: int
    title: str
    right_answers_to_win: int
    wrong_answers_to_lose: int


class SessionModel(db):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    started_by_vk_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="Prepared")
    move_number = Column(Integer, nullable=False, default=0)
    winner_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True)
    response_time = Column(Integer, nullable=False, default=30)
    session_duration = Column(Integer, nullable=False, default=1800)
    started_at = Column(DateTime(timezone=False), server_default=func.now())
    start_message_id = Column(Integer, unique=True)
    answering_player_vk_id = Column(Integer, nullable=True)
    finished_at = Column(DateTime(timezone=False))
    winner = relationship(
        "PlayerModel",
        back_populates="won_sessions"
    )
    players = relationship(
        "PlayersStatusModel",
        back_populates="session"
    )

    def to_dc(self) -> Session:
        return Session(
            id=self.id,
            chat_id=self.chat_id,
            started_by=self.started_by_vk_id,
            status=self.status,
            move_number=self.move_number,
            response_time=self.response_time,
            session_duration=self.session_duration,
            start_message_id=self.start_message_id,
            started_at=self.started_at,
            answering_player_vk_id=self.answering_player_vk_id,
            finished_at=self.finished_at,
            winner_id=self.winner_id
        )


class PlayerModel(db):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    games_count = Column(Integer, nullable=False, default=0)
    wins_count = Column(Integer, nullable=False, default=0)
    loses_count = Column(Integer, nullable=False, default=0)
    won_sessions = relationship(
        "SessionModel",
        back_populates="winner"
    )
    statuses = relationship(
        "PlayersStatusModel",
        back_populates="player"
    )

    def to_dc(self) -> Player:
        return Player(
            id=self.id,
            vk_id=self.vk_id ,
            first_name=self.first_name,
            last_name=self.last_name,
            games_count=self.games_count,
            wins_count=self.wins_count,
            loses_count=self.loses_count
        )


class PlayersStatusModel(db):
    __tablename__ = "players_status"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False, unique=False)
    session_id = Column(
        Integer,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False)
    difficulty_id = Column(
        Integer,
        ForeignKey("difficulties.id", ondelete="CASCADE"),
        nullable=False
    )
    right_answers = Column(Integer, nullable=False, default=0)
    wrong_answers = Column(Integer, nullable=False, default=0)
    is_won = Column(Boolean, nullable=False, default=False)
    is_lost = Column(Boolean, nullable=False, default=False)
    session = relationship(
        "SessionModel",
        back_populates="players"
    )
    player = relationship(
        "PlayerModel",
        back_populates="statuses"
    )
    difficulty = relationship(
        "DifficultyModel",
        back_populates="current_players"
    )

    def to_dc(self) -> PlayerStatus:
        return PlayerStatus(
            id=self.id,
            player_id=self.player_id,
            session_id=self.session_id,
            difficulty_id=self.difficulty_id,
            right_answers=self.right_answers,
            wrong_answers=self.wrong_answers,
            is_lost=self.is_lost,
            is_won=self.is_won
        )

    def to_nested_dc(self) -> PlayerStatusNested:
        return PlayerStatusNested(
            id=self.id,
            player_id=self.player_id,
            session_id=self.session_id,
            difficulty_id=self.difficulty_id,
            right_answers=self.right_answers,
            wrong_answers=self.wrong_answers,
            is_won=self.is_won,
            is_lost=self.is_lost,
            player=self.player.to_dc()
        )


class DifficultyModel(db):
    __tablename__ = "difficulties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, unique=True)
    right_answers_to_win = Column(Integer, nullable=False)
    wrong_answers_to_lose = Column(Integer, nullable=False)
    current_players = relationship(
        "PlayersStatusModel",
        back_populates="difficulty"
    )
    questions = relationship("QuestionModel", back_populates="difficulty")

    def to_dc(self) -> Difficulty:
        return Difficulty(
            id=self.id,
            title=self.title,
            right_answers_to_win=self.right_answers_to_win,
            wrong_answers_to_lose=self.wrong_answers_to_lose
        )
