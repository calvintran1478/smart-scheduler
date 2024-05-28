from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from typing import Optional
from datetime import datetime
import enum

class RepeatRuleEnum(str, enum.Enum):
    NEVER = "NEVER"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

class Event(UUIDBase):
    __tablename__ = "events"
    __table_args__ = (CheckConstraint("start_time <= end_time", name="start_time_lte_end_time"),)

    summary: Mapped[str]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    repeat_rule: Mapped[str] = mapped_column(Enum(RepeatRuleEnum, name="repeat_rule"), default="NEVER")
    until: Mapped[Optional[datetime]]
    description: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="events", lazy="selectin")