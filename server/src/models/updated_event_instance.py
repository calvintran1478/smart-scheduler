from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint, ForeignKey
from litestar.contrib.sqlalchemy.base import UUIDBase
from datetime import datetime
from typing import Optional

class UpdatedEventInstance(UUIDBase):
    __tablename__ = "updated_event_instances"
    __table_args__ = (UniqueConstraint("recurrence_id", "event_id", name="uq_instance_event_id_recurrence_id"),)

    summary: Mapped[str]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    description: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    recurrence_id: Mapped[datetime]
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE", onupdate="CASCADE"))

    event: Mapped["Event"] = relationship(back_populates="updated_event_instances")