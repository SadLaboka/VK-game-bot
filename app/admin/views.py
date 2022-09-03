import time

from aiohttp.web_exceptions import HTTPNotImplemented
from aiohttp_session import new_session

from app.admin.schemes import (
    AdminRequestSchema,
    AdminResponseSchema,
    AdminResponseDataSchema)
from app.web.app import View

from aiohttp_apispec import docs, request_schema, response_schema

from app.web.mixins import AuthRequiredMixin
from app.web.utils import authenticate, json_response


class AdminLoginView(View):
    @docs(tags=['admin'],
          summary='Auth',
          description='Authorizes the admin in the system')
    @request_schema(AdminRequestSchema)
    @response_schema(AdminResponseSchema, 200)
    async def post(self):
        data = self.request['data']
        email = data['email']
        password = data['password']
        app = self.request.app

        admin = await authenticate(email, password, app)
        session = await new_session(self.request)
        session['last_visit'] = time.time()
        session['email'] = email

        return json_response(data=AdminResponseDataSchema().dump(admin))

    async def get(self):
        raise HTTPNotImplemented(text='Get method does not implemented')


@docs(tags=['admin'],
      summary='Who am i?',
      description='Get current admin from database')
@response_schema(AdminResponseSchema, 200)
class AdminCurrentView(View, AuthRequiredMixin):

    async def get(self):
        admin = await self.check_auth()

        return json_response(data=AdminResponseDataSchema().dump(admin))

    async def post(self):
        raise HTTPNotImplemented(text='Post method does not implemented')
