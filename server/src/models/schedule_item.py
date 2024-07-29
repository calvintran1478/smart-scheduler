from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, CheckConstraint
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import time
import enum

class ScheduleItemTypeEnum(str, enum.Enum):
    EVENT = "EVENT"
    HABIT = "HABIT"
    SLEEP = "SLEEP"
    FOCUS_SESSION = "FOCUS_SESSION"

class ScheduleItem(UUIDBase):
    __tablename__ = "schedule_items"
    __table_args__ = (CheckConstraint("start_time <= end_time", name="start_time_lte_end_time"),)

    name: Mapped[str]
    start_time: Mapped[time]
    end_time: Mapped[time]
    schedule_item_type: Mapped[str] = mapped_column(Enum(ScheduleItemTypeEnum, name="schedule_item_type"))
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id", ondelete="CASCADE", onupdate="CASCADE"))

    schedule: Mapped["Schedule"] = relationship(back_populates="schedule_items")