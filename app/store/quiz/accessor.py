from typing import Optional

from aiohttp.web_exceptions import HTTPConflict, HTTPUnprocessableEntity, HTTPNotFound

from app.base.base_accessor import BaseAccessor
from app.quiz.models import Theme, Question, Answer


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        if await self.get_theme_by_title(title):
            raise HTTPConflict
        theme = Theme(id=self.app.database.next_theme_id, title=str(title))
        self.app.database.themes.append(theme)
        return theme

    async def get_theme_by_title(self, title: str) -> Optional[Theme]:
        themes = self.app.database.themes
        for theme in themes:
            if theme.title == title:
                return theme
        return None

    async def get_theme_by_id(self, id_: int) -> Optional[Theme]:
        themes = self.app.database.themes
        for theme in themes:
            if theme.id == id_:
                return theme
        return None

    async def list_themes(self) -> list[Theme]:
        themes = self.app.database.themes
        return themes

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        questions = await self.list_questions()
        for question in questions:
            if question.title == title:
                return question

        return None

    async def create_question(
        self, title: str, theme_id: int, answers: list[Answer]
    ) -> Question:
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

        question = Question(
            id=self.app.database.next_question_id,
            title=title,
            theme_id=theme_id,
            answers=answers)
        self.app.database.questions.append(question)
        return question

    async def list_questions(self, theme_id: Optional[int] = None) -> list[Question]:
        questions = self.app.database.questions
        if theme_id is None:
            return questions

        questions_by_theme_id = []
        for question in questions:
            if question.theme_id == int(theme_id):
                questions_by_theme_id.append(question)

        return questions_by_theme_id
