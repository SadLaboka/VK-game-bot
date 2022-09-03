from aiohttp.web_exceptions import (
    HTTPNotImplemented,
    HTTPConflict,
    HTTPNotFound
)
from aiohttp_apispec import (
    request_schema, response_schema, docs, querystring_schema
)
from sqlalchemy.exc import IntegrityError

from app.quiz.schemes import (
    ThemeSchema, ThemeIdSchema, ThemeListResponseSchema,
    QuestionSchema, QuestionResponseSchema,
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
        try:
            theme = await self.store.quizzes.create_theme(title=title)
            return json_response(data=ThemeSchema().dump(theme))
        except IntegrityError as e:
            if e.orig.pgcode == "23505":
                raise HTTPConflict(text="Theme is already exists")

    async def get(self):
        raise HTTPNotImplemented(text='Get method does not implemented')


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

    async def post(self):
        raise HTTPNotImplemented(text='Post method does not implemented')


class QuestionAddView(View, AuthRequiredMixin):
    @docs(tags=['quiz'],
          summary='Add question',
          description='Add new question to the database')
    @request_schema(QuestionSchema)
    @response_schema(QuestionResponseSchema, 200)
    async def post(self):
        await self.check_auth()

        data = self.request['data']
        try:
            question = await self.store.quizzes.create_question(
                title=data['title'],
                theme_id=data['theme_id'],
                answers=data['answers']
            )
            return json_response(data=QuestionSchema().dump(question))
        except IntegrityError as e:
            if e.orig.pgcode == '23503':
                raise HTTPNotFound(text='Theme does not exists')
            elif e.orig.pgcode == '23502':
                raise HTTPNotFound(text='No theme id specified')
            elif e.orig.pgcode == '23505':
                raise HTTPConflict(text='Question is already exists')

    async def get(self):
        raise HTTPNotImplemented(text='Get method does not implemented')


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

        return json_response(data={
            'questions': [
                QuestionSchema().dump(question) for question in questions
            ]})

    async def post(self):
        raise HTTPNotImplemented(text='Post method does not implemented')
