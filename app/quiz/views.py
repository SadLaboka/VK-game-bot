from aiohttp_apispec import request_schema, response_schema, docs

from app.quiz.schemes import (
    ThemeSchema, ThemeIdSchema,
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


class ThemeListView(View):
    async def get(self):
        raise NotImplementedError


class QuestionAddView(View):
    async def post(self):
        raise NotImplementedError


class QuestionListView(View):
    async def get(self):
        raise NotImplementedError
