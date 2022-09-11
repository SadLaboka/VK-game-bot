from typing import Optional, List

from aiohttp.web_exceptions import HTTPUnprocessableEntity

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Theme, Question, Answer, ThemeModel, QuestionModel, AnswerModel
)


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        theme = ThemeModel(title=title)
        async with self.app.database.session.begin() as conn:
            conn.add(theme)

        return theme.to_dc()

    async def get_theme_by_title(self, title: str) -> Optional[Theme]:
        async with self.app.database.session.begin() as conn:
            theme = (
                await conn.scalars(
                    select(ThemeModel).where(ThemeModel.title == title)
                )).first()
        return theme.to_dc() if theme else None

    async def get_theme_by_id(self, id_: int) -> Optional[Theme]:
        async with self.app.database.session.begin() as conn:
            theme = (
                await conn.scalars(
                    select(ThemeModel).where(ThemeModel.id == id_)
                )).first()
        return theme.to_dc() if theme else None

    async def list_themes(self) -> List[Theme]:
        async with self.app.database.session.begin() as conn:
            themes = (await conn.scalars(select(ThemeModel))).fetchall()
        return [theme.to_dc() for theme in themes]

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        async with self.app.database.session.begin() as conn:
            question = (
                await conn.scalars(
                    select(QuestionModel)
                    .where(QuestionModel.title == title)
                    .options(joinedload(QuestionModel.answers)))
            ).first()
        return question.to_dc() if question else None

    async def create_question(
            self, title: str, theme_id: int, answers: List[Answer]
    ) -> Question:
        correct_answers = 0
        for answer in answers:
            if answer['is_correct']:
                correct_answers += 1

        if len(answers) < 2:
            raise HTTPUnprocessableEntity(
                text='Wrong number of answers'
            )

        if correct_answers != 1:
            raise HTTPUnprocessableEntity(
                text='Wrong number of correct answers'
            )

        question = QuestionModel(
            title=title,
            theme_id=theme_id,
            answers=[
                AnswerModel(
                    title=answer['title'],
                    is_correct=answer['is_correct']
                )
                for answer in answers
            ],
        )
        async with self.app.database.session.begin() as conn:
            conn.add(question)

        return question.to_dc()

    async def list_questions(
            self, theme_id: Optional[int] = None
    ) -> List[Question]:
        query = select(QuestionModel)
        if theme_id:
            theme_id = int(theme_id)
            query = query.where(QuestionModel.theme_id == theme_id)
        async with self.app.database.session.begin() as conn:
            questions = await conn.scalars(
                query.options(joinedload(QuestionModel.answers))
            )

        return [q.to_dc() for q in questions.unique()]
