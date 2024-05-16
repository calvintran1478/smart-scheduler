from sqlalchemy.orm import Mapped, mapped_column, relationship
from litestar.contrib.sqlalchemy.base import UUIDBase
from typing import Optional

from models.preferred_time_interval import PreferredTimeInterval

class User(UUIDBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    refresh_token_number: Mapped[Optional[int]]

    preference: Mapped["Preference"] = relationship(back_populates="user")