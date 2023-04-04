from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from sqlalchemy import Column, Integer, Text

from kts_backend.store.database.sqlalchemy_base import db


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Optional[dict]) -> Optional["Admin"]:
        return cls(id=session["admin"]["id"], email=session["admin"]["email"])


class AdminModel(db):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    email = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)

    def __repr__(self):
        return f"AdminModel(id='{self.id}', email='{self.email}', password='{self.password}')"