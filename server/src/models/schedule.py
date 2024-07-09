from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import date

class Schedule(UUIDBase):
    __tablename__ = "schedules"

    date: Mapped[date]
    requires_refresh: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    schedule_items: Mapped[list["ScheduleItem"]] = relationship(back_populates="schedule", lazy="selectin", passive_deletes=True, cascade="all, delete-orphan")
    user: Mapped["User"] = relationship(back_populates="schedule")