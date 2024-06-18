from litestar import Controller, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.dto import DTOData
from litestar.exceptions import ClientException, NotFoundException
from litestar.di import Provide

from models.user import User
from models.event import Event
from models.updated_event_instance import UpdatedEventInstance
from models.exception_date import ExceptionDate
from domain.users.events.repositories import EventRepository, ExceptionDateRepository, UpdatedEventInstanceRepository
from domain.users.events.dependencies import provide_events_repo, provide_exception_dates_repo, provide_updated_event_instances_repo, provide_event
from domain.users.events.schemas import CreateEventInput, UpdateEventInput
from domain.users.events.dtos import UpdateEventDTO, EventDTO
from domain.users.events.hooks import after_event_get_request
from domain.users.events.validators import validate_new_times, validate_event_query_parameters
from lib.time import convert_to_utc
from lib.event import get_updated_event_instance_from_event

from typing import Optional
from datetime import datetime, time

class EventController(Controller):
    dependencies = {
        "events_repo": Provide(provide_events_repo),
        "exception_dates_repo": Provide(provide_exception_dates_repo),
        "updated_event_instances_repo": Provide(provide_updated_event_instances_repo),
        "event": Provide(provide_event)
    }

    @post(path="/", return_dto=EventDTO)
    async def create_event(self, data: CreateEventInput, user: User, events_repo: EventRepository) -> Event:
        # Create event for the user
        event = Event(
            user_id=user.id,
            summary=data.summary,
            start_time=convert_to_utc(data.timezone, data.start_time),
            end_time=convert_to_utc(data.timezone, data.end_time),
            repeat_rule=data.repeat_rule,
            until=convert_to_utc(data.timezone, datetime.combine(data.until, time(23, 59, 59))),
            description=data.description,
            location=data.location,
        )

        await events_repo.add(event, auto_commit=True)

        return event
    
    @get(path="/", return_dto=EventDTO, after_request=after_event_get_request)
    async def get_events(self, user: User, events_repo: EventRepository, start: str, end: str, timezone: str) -> list[Event]:
        # Validate query paramters
        start_time, end_time, timezone_format = validate_event_query_parameters(start, end, timezone)

        # Search for events in the given range
        events = await events_repo.get_events_in_range(user.id, start_time, end_time, timezone_format)
        return events

    @patch(path="/{event_id:str}", dto=UpdateEventDTO, status_code=HTTP_204_NO_CONTENT)
    async def update_event(
        self,
        data: DTOData[UpdateEventInput],
        event: Event,
        events_repo: EventRepository,
        exception_dates_repo: ExceptionDateRepository,
        updated_event_instances_repo: UpdatedEventInstanceRepository,
        start: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> None:
        # Update input values
        update_data = data.create_instance()

        # Update all instances of the event
        if (event.repeat_rule == "NEVER" or (start == timezone == None)):
            # No time change
            if (update_data.timezone == None):
                if (update_data.start_time != None or update_data.end_time != None or update_data.until != None):
                    raise ClientException(detail="Missing required timezone info for time change")
                data.update_instance(event)

            # Time change
            else:
                old_until = event.until
                new_start_time, new_end_time, new_until = validate_new_times(update_data, event)
                data.update_instance(
                    event,
                    start_time=new_start_time,
                    end_time=new_end_time,
                    until=new_until
                )

                # Remove updated instances after the new until value (if changed to be earlier)
                if (old_until == None and new_until != None or old_until != None and new_until < old_until):
                    await updated_event_instances_repo.delete_after_date(event.id, new_until)

        # Update a particular instance of the event
        elif (start != None and timezone != None):
            # Convert start and timezone parameters
            start_time = validate_event_query_parameters(start, None, timezone)[0]

            # Search for event instance
            instance_exists, instance_type = await events_repo.check_instance(event, start_time, exception_dates_repo, updated_event_instances_repo)
            if (not instance_exists):
                raise NotFoundException(detail="Event not found")

            # Add new updated instance or search for one to modify
            updated_instance = None
            if (instance_type == "event_instance"):
                updated_instance = get_updated_event_instance_from_event(event, start_time)
            elif (instance_type == "updated_instance"):
                updated_instance = await updated_event_instances_repo.get_one_or_none(recurrence_id=start_time, event_id=event.id)

            # No time change
            if (update_data.timezone == None):
                if (update_data.start_time != None or update_data.end_time != None):
                    raise ClientException(detail="Missing required timezone info for time change")
                data.update_instance(updated_instance)

            # Time change
            else:
                new_start_time, new_end_time, _ = validate_new_times(update_data, event)
                data.update_instance(
                    updated_instance,
                    start_time=new_start_time,
                    end_time=new_end_time
                )

            # Save instance to database if one was created
            if (instance_type == "event_instance"):
                await updated_event_instances_repo.add(updated_instance, auto_commit=True)

        # Handle missing query parameters
        else:
            raise ClientException(detail="Start and timezone query parameters must both appear or not at all")
    
    @delete(path="/{event_id:str}")
    async def remove_event(
        self,
        event: Event,
        events_repo: EventRepository,
        exception_dates_repo: ExceptionDateRepository,
        updated_event_instances_repo: UpdatedEventInstanceRepository,
        start: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> None:
        # Delete all instances of the event
        if (event.repeat_rule == "NEVER" or (start == timezone == None)):
            await events_repo.delete(event.id, auto_commit=True)

        # Delete a particular instance of the event
        elif (start != None and timezone != None):
            # Convert start and timezone parameters
            start_time = validate_event_query_parameters(start, None, timezone)[0]

            # Search for event instance
            instance_exists, instance_type = await events_repo.check_instance(event, start_time, exception_dates_repo, updated_event_instances_repo)
            if (not instance_exists):
                raise NotFoundException(detail="Event not found")

            # Add exception date
            exception_date = ExceptionDate(start_time=start_time, event_id=event.id)
            await exception_dates_repo.add(exception_date, auto_commit=True)

            # Delete updated instance if one exists
            if (instance_type == "updated_instance"):
                await updated_event_instances_repo.delete_by_start_time_and_event_id(start_time, event.id)

        # Handle missing query parameters
        else:
            raise ClientException(detail="Start and timezone query parameters must both appear or not at all")