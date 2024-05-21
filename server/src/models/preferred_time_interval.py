from litestar.contrib.sqlalchemy.base import UUIDBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint, ForeignKey
from datetime import time

class PreferredTimeInterval(UUIDBase):
    __tablename__ = "preferred_time_intervals"
    __table_args__ = (CheckConstraint("start_time <= end_time", name="start_time_lte_end_time"),)

    start_time: Mapped[time]
    end_time: Mapped[time]
    preference_id: Mapped[int] = mapped_column(ForeignKey("preferences.id", ondelete="CASCADE", onupdate="CASCADE"))

    preference: Mapped["Preference"] = relationship(back_populates="best_focus_times")