from typing import Optional, List

from aiohttp.web_exceptions import HTTPConflict, HTTPUnprocessableEntity, HTTPNotFound
from sqlalchemy import select

from app.base.base_accessor import BaseAccessor
from app.quiz.models import Theme, Question, Answer, ThemeModel, QuestionModel, AnswerModel


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        same_theme = await self.get_theme_by_title(title)
        if await self.get_theme_by_title(title):
            raise HTTPConflict(text="Theme is already exists")
        theme = ThemeModel(title=title)
        async with self.app.database.session() as conn:
            conn.add(theme)
            await conn.commit()
            await conn.refresh(theme)
        if same_theme:
            raise HTTPConflict(text="Theme is already exists")
        return Theme(id=theme.id, title=theme.title)

    async def get_theme_by_title(self, title: str) -> Optional[Theme]:
        async with self.app.database.session() as conn:
            theme = (await conn.scalars(select(ThemeModel).where(ThemeModel.title == title))).first()
        return Theme(id=theme.id, title=theme.title) if theme else None

    async def get_theme_by_id(self, id_: int) -> Optional[Theme]:
        async with self.app.database.session() as conn:
            theme = (await conn.scalars(select(ThemeModel).where(ThemeModel.id == id_))).first()
        return Theme(id=theme.id, title=theme.title) if theme else None

    async def list_themes(self) -> list[Theme]:
        async with self.app.database.session() as conn:
            themes = (await conn.scalars(select(ThemeModel))).fetchall()
        list_themes = []
        for theme in themes:
            list_themes.append(Theme(
                id=theme.id,
                title=theme.title
            ))
        return list_themes

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        async with self.app.database.session() as conn:
            question = (await conn.scalars(select(QuestionModel).where(QuestionModel.title == title))).first()
        if question:
            answers = await self.get_answers_by_question(question_id=question.id)
            return Question(
                id=question.id,
                theme_id=question.theme_id,
                title=question.title,
                answers=answers
            )

    async def create_question(
            self, title: str, theme_id: int, answers: List[Answer]
    ) -> Question:
        correct_answers = 0
        for answer in answers:
            if answer['is_correct']:
                correct_answers += 1

        if len(answers) < 2:
            raise HTTPUnprocessableEntity(text='Wrong number of answers')

        if correct_answers != 1:
            raise HTTPUnprocessableEntity(text='Wrong number of correct answers')

        if theme_id and not await self.get_theme_by_id(theme_id):
            raise HTTPNotFound(text='Theme does not exists')
        #
        # if await self.get_question_by_title(title) is not None:
        #     raise HTTPConflict(text='Question is already exists')

        question = QuestionModel(
            title=title,
            theme_id=theme_id)
        async with self.app.database.session() as conn:
            conn.add(question)
            await conn.commit()
            await conn.refresh(question)
        new_question = Question(
            id=question.id,
            theme_id=question.theme_id,
            title=question.title,
            answers=(await self.create_answers(
                question_id=question.id, answers=answers))
        )
        return new_question

    async def create_answers(self, question_id, answers: list[Answer]) -> List[Answer]:
        async with self.app.database.session() as conn:
            for answer in answers:
                new_answer = AnswerModel(
                    title=answer["title"],
                    is_correct=answer["is_correct"],
                    question_id=question_id
                )
                conn.add(new_answer)
                await conn.commit()

        return answers

    async def list_questions(self, theme_id: Optional[int] = None) -> List[Question]:
        async with self.app.database.session() as conn:
            if theme_id is None:
                questions = (await conn.scalars(select(QuestionModel))).fetchall()
            else:
                theme_id = int(theme_id)
                questions = (
                    await conn.scalars(select(QuestionModel).where(QuestionModel.theme_id == theme_id))).fetchall()

        list_questions = []
        for question in questions:
            answers = await self.get_answers_by_question(question.id)
            list_questions.append(Question(
                id=question.id,
                title=question.title,
                theme_id=question.theme_id,
                answers=answers
            ))

        return list_questions

    async def get_answers_by_question(self, question_id: int) -> List[Answer]:
        async with self.app.database.session() as conn:
            answers = (await conn.scalars(select(AnswerModel).where(AnswerModel.question_id == question_id))).fetchall()

        list_answers = []
        for answer in answers:
            list_answers.append(Answer(
                title=answer.title,
                is_correct=answer.is_correct
            ))
        return list_answers
