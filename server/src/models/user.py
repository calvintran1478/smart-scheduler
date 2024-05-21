from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint
from litestar.contrib.sqlalchemy.base import UUIDBase

from models.preferred_time_interval import PreferredTimeInterval

class User(UUIDBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(CheckConstraint("char_length(password) >= 8", name="password_length_gte_8"))
    first_name: Mapped[str]
    last_name: Mapped[str]

    devices: Mapped[list["Device"]] = relationship(back_populates="user", passive_deletes=True)
    preference: Mapped["Preference"] = relationship(back_populates="user", passive_deletes=True)