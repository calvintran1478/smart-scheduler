from sqlalchemy.orm import Mapped, mapped_column
from litestar.contrib.sqlalchemy.base import UUIDBase

class User(UUIDBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    refresh_token_number: Mapped[int | None] = mapped_column(nullable=True, default=None)