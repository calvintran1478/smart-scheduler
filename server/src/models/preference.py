from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, CheckConstraint
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import time
from typing import Optional

from models.user import User

class Preference(UUIDBase):
    __tablename__ = "preferences"

    wake_up_time: Mapped[Optional[time]]
    sleep_time: Mapped[Optional[time]]
    start_of_work_day: Mapped[Optional[time]]
    end_of_work_day: Mapped[Optional[time]]
    break_length: Mapped[Optional[int]] = mapped_column(CheckConstraint("break_length >= 0", name="break_length_gte_0"))
    tend_to_procrastinate: Mapped[Optional[bool]]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    best_focus_times: Mapped[list["PreferredTimeInterval"]] = relationship(back_populates="preference", lazy="selectin", passive_deletes=True)
    user: Mapped["User"] = relationship(back_populates="preference")