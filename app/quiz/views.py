from aiohttp_apispec import request_schema, response_schema, docs, querystring_schema

from app.quiz.schemes import (
    ThemeSchema, ThemeIdSchema, ThemeListResponseSchema, QuestionSchema, QuestionResponseSchema,
    ListQuestionResponseSchema, QuestionGetRequestSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(View, AuthRequiredMixin):
    @docs(tags=['quiz'],
          summary='Add theme',
          description='Add new theme to the database')
    @request_schema(ThemeSchema)
    @response_schema(ThemeIdSchema, 200)
    async def post(self):
        await self.check_auth()

        title = self.data['title']
        theme = await self.store.quizzes.create_theme(title=title)
        return json_response(data=ThemeSchema().dump(theme))


@docs(tags=['quiz'],
      summary='Show themes',
      description='Show all themes from database')
@response_schema(ThemeListResponseSchema, 200)
class ThemeListView(View, AuthRequiredMixin):
    async def get(self):
        await self.check_auth()

        themes = await self.store.quizzes.list_themes()
        return json_response(data={
            'themes': [ThemeSchema().dump(theme) for theme in themes]})


class QuestionAddView(View, AuthRequiredMixin):
    @docs(tags=['quiz'],
          summary='Add question',
          description='Add new question to the database')
    @request_schema(QuestionSchema)
    @response_schema(QuestionResponseSchema, 200)
    async def post(self):
        await self.check_auth()

        data = self.request['data']
        question = await self.store.quizzes.create_question(
            title=data['title'],
            theme_id=data['theme_id'],
            answers=data['answers']
        )
        print(question)
        return json_response(data=QuestionSchema().dump(question))


class QuestionListView(View, AuthRequiredMixin):
    @docs(tags=['quiz'],
          summary='Show themes',
          description='Show all themes from database')
    @querystring_schema(QuestionGetRequestSchema)
    @response_schema(ListQuestionResponseSchema, 200)
    async def get(self):
        await self.check_auth()

        theme_id = self.request.query.get('theme_id')
        questions = await self.store.quizzes.list_questions(theme_id)
        print(questions)

        return json_response(data={
            'themes': [QuestionSchema().dump(question) for question in questions]})
