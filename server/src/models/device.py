from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from typing import Optional

class Device(UUIDBase):
    __tablename__ = "devices"

    refresh_token_number: Mapped[Optional[int]]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))
    device_id: Mapped[str] = mapped_column(unique=True)

    user: Mapped["User"] = relationship(back_populates="devices")