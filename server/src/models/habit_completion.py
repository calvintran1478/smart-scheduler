from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, UniqueConstraint, ForeignKeyConstraint
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import date
from uuid import UUID

class HabitCompletion(UUIDBase):
    __tablename__ = "habit_completions"
    __table_args__ = (UniqueConstraint("completion_date", "habit_name", "user_id", name="uq_user_habit_completion_date"), ForeignKeyConstraint(["habit_name", "user_id"], ["habits.name", "habits.user_id"], ondelete="CASCADE", onupdate="CASCADE"))

    completion_date: Mapped[date]
    count: Mapped[int] = mapped_column(CheckConstraint("count >= 1", name="count_gte_1"), default=1)
    habit_name: Mapped[str]
    user_id: Mapped[UUID]

    habit: Mapped["Habit"] = relationship(back_populates="completions")