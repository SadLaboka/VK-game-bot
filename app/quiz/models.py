from dataclasses import dataclass
from typing import Optional, List

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Theme:
    id: Optional[int]
    title: str


@dataclass
class Answer:
    title: str
    is_correct: bool

    def __getitem__(self, item):
        return getattr(self, item)


@dataclass
class Question:
    id: int
    title: str
    theme_id: int
    answers: List[Answer]


class ThemeModel(db):
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(60), nullable=False, unique=True)
    questions = relationship(
        "QuestionModel",
        back_populates='themes',
        cascade="all, delete",
        passive_deletes=True
    )

    def to_dc(self) -> Theme:
        return Theme(
            id=self.id,
            title=self.title
        )


class QuestionModel(db):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(60), nullable=False, unique=True)
    theme_id = Column(
        Integer,
        ForeignKey("themes.id", ondelete="CASCADE"), nullable=False
    )
    themes = relationship("ThemeModel", back_populates='questions')
    answers = relationship("AnswerModel", back_populates='questions')

    def to_dc(self) -> Question:
        return Question(
            id=self.id,
            title=self.title,
            theme_id=self.theme_id,
            answers=[a.to_dc() for a in self.answers],
        )


class AnswerModel(db):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(60), nullable=False)
    is_correct = Column(Boolean(), nullable=False)
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    questions = relationship("QuestionModel", back_populates='answers')

    def to_dc(self) -> Answer:
        return Answer(
            title=self.title,
            is_correct=self.is_correct
        )
