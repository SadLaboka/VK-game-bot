from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from sqlalchemy import Column, String, Integer

from app.store.database.sqlalchemy_base import db


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[sha256] = None

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()


class AdminModel(db):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()
