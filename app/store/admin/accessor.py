import typing

from hashlib import sha256

from sqlalchemy import insert, select
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.admin.models import Admin, AdminModel

if typing.TYPE_CHECKING:
    from app.web.app import Application


class NotRegistered(Exception):
    pass


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        email = app.config.admin.email
        password = app.config.admin.password
        encrypted_pass = sha256(password.encode()).hexdigest()
        admin = AdminModel(
            email=email,
            password=encrypted_pass
        )
        try:
            async with self.app.database.session() as conn:
                conn.add(admin)
                await conn.commit()
        except Exception:
            pass

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        async with self.app.database.session() as conn:
            admin = (await conn.scalars(select(AdminModel).where(AdminModel.email == email))).first()

        if admin:
            return admin
        else:
            raise NotRegistered

    async def create_admin(self, id_: int, email: str, password: sha256) -> Admin:
        return Admin(id=id_, email=email, password=password)
