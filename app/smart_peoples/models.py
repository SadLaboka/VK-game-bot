from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, String
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


class SessionModel(db):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    started_by_vk_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="Active")
    winner_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True)
    response_time = Column(Integer, nullable=False, default=30)
    session_duration = Column(Integer, nullable=False, default=1800)
    started_at = Column(DateTime(timezone=False), server_default=func.now())
    finished_at = Column(DateTime(timezone=False))
    winner = relationship(
        "PlayerModel",
        back_populates="won_sessions"
    )
    players = relationship(
        "PlayersStatusModel",
        back_populates="session"
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


class PlayersStatusModel(db):
    __tablename__ = "players_status"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False, unique=True)
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
    session = relationship(
        "SessionModel",
        back_populates="players"
    )
    difficulty = relationship(
        "DifficultyModel",
        back_populates="current_players"
    )
    questions = relationship("QuestionModel", back_populates="difficulty")


class DifficultyModel(db):
    __tablename__ = "difficulties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    right_answers_to_win = Column(Integer, nullable=False)
    wrong_answers_to_lose = Column(Integer, nullable=False)
    current_players = relationship(
        "PlayersStatusModel",
        back_populates="difficulty"
    )
