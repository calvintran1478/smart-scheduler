from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, UniqueConstraint, ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from lib.time import MINUTES_PER_DAY
import enum

class RepeatIntervalEnum(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"

class TimePrefererenceEnum(str, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"

class Habit(UUIDBase):
    __tablename__ = "habits"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_habits_user_id_name"),)

    name: Mapped[str]
    frequency: Mapped[int] = mapped_column(CheckConstraint("frequency >= 1", name="frequency_gte_1"))
    duration: Mapped[int] = mapped_column(CheckConstraint(f"1 <= duration AND duration <= {MINUTES_PER_DAY}", name="duration_positive_and_within_1_day"))
    repeat_interval: Mapped[str] = mapped_column(Enum(RepeatIntervalEnum, name="repeat_interval"))
    morning_preferred: Mapped[bool] = mapped_column(default=False)
    afternoon_preferred: Mapped[bool] = mapped_column(default=False)
    evening_preferred: Mapped[bool] = mapped_column(default=False)
    night_preferred: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="habits")
    completions: Mapped[list["HabitCompletion"]] = relationship(back_populates="habit", passive_deletes=True)
