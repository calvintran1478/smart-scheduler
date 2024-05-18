from litestar.contrib.sqlalchemy.base import UUIDBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey
from datetime import time

class PreferredTimeInterval(UUIDBase):
    __tablename__ = "preferred_time_intervals"

    start_time: Mapped[time]
    end_time: Mapped[time]
    preference_id: Mapped[int] = mapped_column(ForeignKey("preferences.id", ondelete="CASCADE", onupdate="CASCADE"))

    preference: Mapped["Preference"] = relationship(back_populates="best_focus_times")