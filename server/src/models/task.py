from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, ForeignKeyConstraint, CheckConstraint

from litestar.contrib.sqlalchemy.base import UUIDBase

from datetime import datetime, time
from typing import Optional

class Task(UUIDBase):
    __tablename__ = "tasks"

    name: Mapped[str]
    deadline: Mapped[datetime]
    time_estimate: Mapped[time]
    minutes_completed: Mapped[int] = mapped_column(CheckConstraint("minutes_completed >= 0", name="minutes_completed_gte_0"), default=0)
    done: Mapped[bool] = mapped_column(default=False)
    tag_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tags.id", ondelete="SET NULL", onupdate="SET NULL"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="tasks")
    tag: Mapped[Optional["Tag"]] = relationship(back_populates="tasks", lazy="selectin")