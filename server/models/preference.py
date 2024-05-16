from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import time
from typing import Optional

from models.user import User

class Preference(UUIDBase):
    __tablename__ = "preferences"

    wake_up_time: Mapped[Optional[time]]
    sleep_time: Mapped[Optional[time]]
    break_length: Mapped[Optional[time]]
    tend_to_procrastinate: Mapped[Optional[bool]]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    best_focus_times: Mapped[list["PreferredTimeInterval"]] = relationship(back_populates="preference")
    user: Mapped["User"] = relationship(back_populates="preference")