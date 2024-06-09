from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import delete, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from uuid import UUID
from models.event import Event
from models.exception_date import ExceptionDate
from models.updated_event_instance import UpdatedEventInstance

class ExceptionDateRepository(SQLAlchemyAsyncRepository[ExceptionDate]):
    """Exception Date repository"""

    model_type = ExceptionDate

class UpdatedEventInstanceRepository(SQLAlchemyAsyncRepository[UpdatedEventInstance]):
    """Updated Event Instance repository"""

    model_type = UpdatedEventInstance

    async def delete_by_start_time_and_event_id(self, start_time: datetime, event_id: UUID) -> None:
        try:
            await self.session.execute(statement=delete(UpdatedEventInstance).where(and_(UpdatedEventInstance.recurrence_id == start_time, UpdatedEventInstance.event_id == event_id)))
        except IntegrityError:
            await self.session.rollback()
        else:
            await self.session.commit()

class EventRepository(SQLAlchemyAsyncRepository[Event]):
    """Event repository"""

    model_type = Event

    async def check_instance(
        self,
        event: Event,
        start_time: datetime,
        exception_dates_repo: ExceptionDateRepository,
        updated_event_instances_repo: UpdatedEventInstanceRepository
    ) -> tuple[bool, str]:
        """Assumes event is recurring"""
        # Check if instance was deleted
        deleted = await exception_dates_repo.exists(start_time=start_time, event_id=event.id)
        if deleted:
            return False, ""

        # Check for updated instance
        updated_instance_exists = await updated_event_instances_repo.exists(recurrence_id=start_time, event_id=event.id)
        if updated_instance_exists:
            return True, "updated_instance"

        # Handle general event case
        same_time = (event.start_time.time() == start_time.time())
        same_day = (event.start_time.day == start_time.day)
        same_month = (event.start_time.month == start_time.month)
        same_week_day = (event.start_time.weekday() == start_time.weekday())

        event_instance_exists = (event.repeat_rule == "DAILY" and same_time) or \
            (event.repeat_rule == "WEEKLY" and same_week_day and same_time) or \
            (event.repeat_rule == "MONTHLY" and same_day and same_time) or \
            (event.repeat_rule == "YEARLY" and same_month and same_day and same_time)

        return event_instance_exists, ("event_instance" if event_instance_exists else "")