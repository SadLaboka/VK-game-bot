from aiohttp.web_exceptions import HTTPNotImplemented
from aiohttp_apispec import docs, response_schema, querystring_schema

from app.smart_peoples.schemes import SessionResponseSchema, SessionGetRequestSchema, SessionSchema, \
    PlayersStatusesGetRequestSchema, PlayerStatusResponseSchema, PlayerStatusSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class SessionsListView(View, AuthRequiredMixin):
    @docs(tags=['game'],
          summary='Show sessions',
          description='Show all game-sessions from database')
    @querystring_schema(SessionGetRequestSchema)
    @response_schema(SessionResponseSchema, 200)
    async def get(self):
        await self.check_auth()

        page = self.request.query.get("page")
        sessions = await self.store.game.get_sessions_by_page(page)

        return json_response(data={
            'sessions': [
                SessionSchema().dump(session) for session in sessions
            ]
        })

    async def post(self):
        raise HTTPNotImplemented(text='Post method does not implemented')


class PlayersStatusesListView(View, AuthRequiredMixin):
    @docs(tags=['game'],
          summary='Show players statuses',
          description='Show all players statuses in selected session')
    @querystring_schema(PlayersStatusesGetRequestSchema)
    @response_schema(PlayerStatusResponseSchema, 200)
    async def get(self):
        await self.check_auth()

        session_id = self.request.query.get("session_id")
        statuses = await self.store.game.get_players_statuses_by_session_id(
            int(session_id))

        return json_response(data={
            'statuses': [
                PlayerStatusSchema().dump(status) for status in statuses
            ]
        })

    async def post(self):
        raise HTTPNotImplemented(text='Post method does not implemented')
