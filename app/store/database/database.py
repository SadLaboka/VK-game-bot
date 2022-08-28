from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from app.quiz.models import Theme, Question, ThemeModel, QuestionModel, AnswerModel
from app.store.database.sqlalchemy_base import db

if TYPE_CHECKING:
    from app.web.app import Application


# @dataclass
# class Database:
#     themes: list[Theme] = field(default_factory=list)
#     admins: list[Admin] = field(default_factory=list)
#     questions: list[Question] = field(default_factory=list)
#
#     @property
#     def next_theme_id(self) -> int:
#         return len(self.themes) + 1
#
#     @property
#     def next_question_id(self) -> int:
#         return len(self.questions) + 1
#
#     def clear(self):
#         self.themes = []
#         self.questions = []


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[AsyncSession] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        self._engine = create_async_engine(
            self.app.config.database_url,
            echo=True,
            future=True
        )
        self.session = sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def disconnect(self, *_: list, **__: dict) -> None:
        pass
