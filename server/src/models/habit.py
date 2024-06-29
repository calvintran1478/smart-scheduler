from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, UniqueConstraint, ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
import enum

class RepeatIntervalEnum(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

class Habit(UUIDBase):
    __tablename__ = "habits"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_habits_user_id_name"),)

    name: Mapped[str]
    frequency: Mapped[int] = mapped_column(CheckConstraint("frequency >= 1", name="frequency_gte_1"))
    duration: Mapped[int] = mapped_column(CheckConstraint("duration >= 1", name="duration_gte_1"))
    repeat_interval: Mapped[str] = mapped_column(Enum(RepeatIntervalEnum, name="repeat_interval"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="habits")
    completions: Mapped[list["HabitCompletion"]] = relationship(back_populates="habit", passive_deletes=True)