import typing

from hashlib import sha256

from sqlalchemy import select
from typing import Optional

from sqlalchemy.exc import IntegrityError

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
            async with self.app.database.session.begin() as conn:
                conn.add(admin)
        except IntegrityError:
            pass

    async def get_by_email(self, email: str) -> Optional[Admin]:
        async with self.app.database.session.begin() as conn:
            admin = (
                await conn.scalars(
                    select(AdminModel).where(AdminModel.email == email)
                )
            ).first()

        if admin:
            return admin
        else:
            raise NotRegistered
