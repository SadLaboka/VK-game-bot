import time

from aiohttp.web_exceptions import HTTPUnauthorized, HTTPForbidden
from aiohttp_session import get_session

from app.admin.models import Admin
from app.store.admin.accessor import NotRegistered


class AuthRequiredMixin:

    async def check_auth(self) -> Admin:
        session = await get_session(self.request)
        if session.new:
            raise HTTPUnauthorized

        email = session['email']
        try:
            admin = await self.store.admins.get_by_email(email)
        except NotRegistered:
            raise HTTPForbidden(text='Admin does not registered')

        session['last_visit'] = time.time()
        return admin.to_dc()
