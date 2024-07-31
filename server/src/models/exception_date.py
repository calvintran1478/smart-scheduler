from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint, ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import datetime

class ExceptionDate(UUIDBase):
    __tablename__ = "exception_dates"
    __table_args__ = (UniqueConstraint("start_time", "event_id", name="uq_exception_date_start_time_event_id"),)

    start_time: Mapped[datetime]
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE", onupdate="CASCADE"))

    event: Mapped["Event"] = relationship(back_populates="exception_dates")