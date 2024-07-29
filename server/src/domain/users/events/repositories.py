from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from uuid import UUID
from math import ceil, floor
from pytz import timezone

from models.event import Event
from models.exception_date import ExceptionDate
from models.updated_event_instance import UpdatedEventInstance
from lib.event import get_event_from_updated_event_instance

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
    
    async def delete_after_date(self, event_id: UUID, date: datetime) -> None:
        try:
            await self.session.execute(statement=delete(UpdatedEventInstance).where(and_(UpdatedEventInstance.event_id == event_id, UpdatedEventInstance.start_time > date)))
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
        # Check instance is a present or future instance of the event
        if (start_time < event.start_time):
            return False, ""

        # Check if instance is past the until value
        if (event.until != None and start_time > event.until):
            return False, ""

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
    
    async def get_events_in_range(
        self,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime,
        timezone_format: timezone,
    ) -> list[Event]:
        # Get singular events
        event_lst = await self.list(Event.user_id == user_id, Event.repeat_rule == "NEVER", Event.start_time < end_time, Event.end_time > start_time)
        for event in event_lst:
            event.start_time = event.start_time.astimezone(timezone_format)
            event.end_time = event.end_time.astimezone(timezone_format)

        # Get recurring daily, weekly, and yearly events
        recurring_events = await self.list(Event.repeat_rule != "NEVER", Event.repeat_rule != "MONTHLY")
        z1 = start_time.timestamp() # range_start
        z2 = end_time.timestamp() # range_end
        for event in recurring_events:
            t1 = event.start_time.timestamp() # event_start
            t2 = event.end_time.timestamp() # event_end

            # Recurrence interval (in seconds)
            tau = 0
            match event.repeat_rule:
                case "DAILY":
                    tau = 86400
                case "WEEKLY":
                    tau = 604800
                case "YEARLY":
                    tau = 31536000

            # Get instance count
            instance_count = floor((event.until.timestamp() - event.start_time.timestamp()) / tau) + 1 if (event.until != None) else -1

            # Solve for values of m
            s1 = (z1 - t2) / tau
            s2 = (z2 - t1) / tau
            m_lower_bound = s1 + 1 if s1.is_integer() else ceil(s1)
            m_upper_bound = s2 if s2.is_integer() else ceil(s2)

            # Bound m to present and future instances limited by the event's until value (if present)
            m_lower_bound = max(m_lower_bound, 0)
            if (instance_count != -1 and m_upper_bound > instance_count):
                m_upper_bound = instance_count

            m_lst = list(range(int(m_lower_bound), int(m_upper_bound)))

            # Produce events
            event_lst += [Event(
                id=event.id,
                summary=event.summary,
                start_time=datetime.fromtimestamp(t1 + tau * m, timezone_format),
                end_time=datetime.fromtimestamp(t2 + tau * m, timezone_format),
                repeat_rule=event.repeat_rule,
                until=event.until,
                description=event.description,
                location=event.location
            ) for m in m_lst]

        # Get recurring monthly events
        recurring_events = await self.list(Event.repeat_rule == "MONTHLY")
        for event in recurring_events:
            if (event.repeat_rule == "MONTHLY"):
                # Event properties
                event_duration = event.end_time - event.start_time

                # Initialize instance paramters and determine search bound
                curr_start_time = event.start_time
                curr_end_time = event.end_time
                time_bound = end_time
                if (event.until != None):
                    time_bound = min(end_time, event.until)

                while (curr_start_time < time_bound):
                    # Check if the event instance and time range intersect
                    if (curr_end_time > start_time and curr_start_time < end_time):
                        event_lst.append(Event(
                            id=event.id,
                            summary=event.summary,
                            start_time=curr_start_time.astimezone(timezone_format),
                            end_time=curr_end_time.astimezone(timezone_format),
                            repeat_rule=event.repeat_rule,
                            until=event.until,
                            description=event.description,
                            location=event.location
                        ))

                    # Increment curr to next event instance
                    found_next = False                  
                    next_month = (curr_start_time.month + 1) % 12
                    next_year = curr_start_time.year if (next_month != 1) else (curr_start_time.year + 1)
                    while (not found_next):
                        try:
                            curr_start_time = curr_start_time.replace(year=next_year, month=next_month)
                            found_next = True
                        except ValueError:
                            next_month = (next_month + 1) % 12
                            if (next_month == 1):
                                next_year += 1

                    curr_end_time = curr_start_time + event_duration

        # Search for updated instances in the given range
        updated_instances_result = await self.session.execute(select(UpdatedEventInstance).join(UpdatedEventInstance.event).join(Event.user).where(and_(Event.user_id == user_id, and_(UpdatedEventInstance.start_time < end_time, UpdatedEventInstance.end_time > start_time))))
        updated_instances = updated_instances_result.scalars().all()
        overridden_instances = [(update_instance.event_id, update_instance.recurrence_id) for update_instance in updated_instances]

        # Search for exception dates in the given range
        event_instances = [(event.id, event.start_time) for event in event_lst]
        exception_dates_result = await self.session.execute(select(ExceptionDate).join(ExceptionDate.event).join(Event.user).where(Event.user_id == user_id))
        exception_dates = exception_dates_result.scalars().all()
        deleted_instances = [(exception_date.event_id, exception_date.start_time) for exception_date in exception_dates if (exception_date.event_id, exception_date.start_time) in event_instances]

        # Filter out events overridden by updated instances, or ones that have been deleted
        instances_to_remove = overridden_instances + deleted_instances
        event_lst = [event for event in event_lst if (event.id, event.start_time) not in instances_to_remove]

        # Replace events with their updated instances
        event_lst += [get_event_from_updated_event_instance(updated_instance, timezone_format) for updated_instance in updated_instances]

        return event_lst