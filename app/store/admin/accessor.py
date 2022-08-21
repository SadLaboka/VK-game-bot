import typing

from hashlib import sha256
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.admin.models import Admin

if typing.TYPE_CHECKING:
    from app.web.app import Application


class NotRegistered(Exception):
    pass


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        email = app.config.admin.email
        password = app.config.admin.password.encode()
        encrypted_pass = app.cryptographer.encrypt(password)

        admins_db = app.database.admins
        admins_count = len(admins_db)
        admin = await self.create_admin(
            id_=admins_count + 1,
            email=email,
            password=encrypted_pass)
        admins_db.append(admin)

    async def get_by_email(self, email: str) -> Optional[Admin]:
        admins = self.app.database.admins
        for admin in admins:
            if admin.email == email:
                return admin
        else:
            raise NotRegistered

    async def create_admin(self, id_: int, email: str, password: sha256) -> Admin:
        return Admin(id=id_, email=email, password=password)
