from typing import Optional, Tuple, List

from aiohttp.web_exceptions import HTTPConflict, HTTPUnprocessableEntity, HTTPNotFound
from sqlalchemy import insert, select

from app.base.base_accessor import BaseAccessor
from app.quiz.models import Theme, Question, Answer, ThemeModel, QuestionModel, AnswerModel
from app.quiz.schemes import QuestionSchema, AnswerSchema


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> ThemeModel:
        if await self.get_theme_by_title(title):
            raise HTTPConflict(text="Theme is already exists")
        theme = ThemeModel(title=title)
        async with self.app.database.session() as conn:
            conn.add(theme)
            await conn.commit()
            await conn.refresh(theme)

        return theme

    async def get_theme_by_title(self, title: str) -> Optional[ThemeModel]:
        async with self.app.database.session() as conn:
            theme = (await conn.scalars(select(ThemeModel).where(ThemeModel.title == title))).first()
        return theme

    async def get_theme_by_id(self, id_: int) -> Optional[ThemeModel]:
        async with self.app.database.session() as conn:
            theme = (await conn.scalars(select(ThemeModel).where(ThemeModel.id == id_))).first()
        return theme

    async def list_themes(self) -> list[ThemeModel]:
        async with self.app.database.session() as conn:
            themes = (await conn.scalars(select(ThemeModel))).fetchall()
        return themes

    async def get_question_by_title(self, title: str) -> Optional[QuestionModel]:
        async with self.app.database.session() as conn:
            question = (await conn.scalars(select(QuestionModel).where(QuestionModel.title == title))).first()
        return question

    async def create_question(
            self, title: str, theme_id: int, answers: list[Answer]
    ) -> QuestionModel:
        correct_answers = 0
        for answer in answers:
            if answer['is_correct']:
                correct_answers += 1

        if len(answers) < 2:
            raise HTTPUnprocessableEntity(text='Wrong number of answers')

        if correct_answers != 1:
            raise HTTPUnprocessableEntity(text='Wrong number of correct answers')

        if not await self.get_theme_by_id(theme_id):
            raise HTTPNotFound(text='Theme does not exists')

        if await self.get_question_by_title(title) is not None:
            raise HTTPConflict(text='Question is already exists')

        question = QuestionModel(
            title=title,
            theme_id=theme_id)
        async with self.app.database.session() as conn:
            conn.add(question)
            await conn.commit()
            await conn.refresh(question)

            for answer in answers:
                new_answer = AnswerModel(
                    title=answer["title"],
                    is_correct=answer["is_correct"],
                    question_id=question.id
                )
                conn.add(new_answer)

            await conn.commit()

        return question

    async def list_questions(self, theme_id: Optional[int] = None) -> list[Question]:
        async with self.app.database.session() as conn:
            if theme_id is None:
                return (await conn.scalars(select(QuestionModel))).fetchall()

            return (await conn.scalars(select(QuestionModel).where(QuestionModel.theme_id == theme_id))).fetchall()

    async def get_answers_by_question(self, question_id: int) -> List[AnswerModel]:
        async with self.app.database.session() as conn:
            answers = (await conn.scalars(select(AnswerModel).where(AnswerModel.question_id == question_id))).fetchall()
        return answers

    async def get_questions_with_answers(self, question: QuestionModel) -> dict:
        question_id = question.id
        answers = await self.get_answers_by_question(question_id)
        result = QuestionSchema().dump(question)
        result['answers'] = [AnswerSchema().dump(answer) for answer in answers]
        return result
