from litestar import Controller, Response, post, patch, delete
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
from domain.users.events.dtos import UpdateEventDTO, EventDTO
from domain.users.events.schemas import CreateEventInput, UpdateEventInput
from domain.users.events.validators import validate_new_times, validate_event_query_parameters
from lib.time import convert_to_utc
from lib.event import get_updated_event_instance_from_event

from typing import Optional

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
            description=data.description,
            location=data.location,
            repeat_rule=data.repeat_rule
        )

        await events_repo.add(event, auto_commit=True)

        return event

    @patch(path="/{event_id:str}", dto=UpdateEventDTO)
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
                if (update_data.start_time != None or update_data.end_time != None):
                    raise ClientException(detail="Missing required timezone info for time change")
                data.update_instance(event)

            # Time change
            else:
                new_start_time, new_end_time = validate_new_times(update_data, event)
                data.update_instance(
                    event,
                    start_time=new_start_time,
                    end_time=new_end_time
                )
            
            return Response(content="", status_code=HTTP_204_NO_CONTENT)

        # Update a particular instance of the event
        elif (start != None and timezone != None):
            # Convert start and timezone parameters
            start, timezone = validate_event_query_parameters(start, timezone)

            # Search for event instance
            start_time = convert_to_utc(timezone, start)
            instance_exists, instance_type = await events_repo.check_instance(event, start_time, exception_dates_repo, updated_event_instances_repo)
            if (not instance_exists):
                raise NotFoundException(detail="Event not found")

            # Add new updated instance or search for one to modify
            updated_instance = None
            if (instance_type == "event_instance"):
                updated_instance = get_updated_event_instance_from_event(event)
            elif (instance_type == "updated_instance"):
                updated_instance = await updated_event_instances_repo.get_one_or_none(recurrence_id=start_time, event_id=event.id)

            # No time change
            if (update_data.timezone == None):
                if (update_data.start_time != None or update_data.end_time != None):
                    raise ClientException(detail="Missing required timezone info for time change")
                data.update_instance(updated_instance)

            # Time change
            else:
                new_start_time, new_end_time = validate_new_times(update_data, event)
                data.update_instance(
                    updated_instance,
                    start_time=new_start_time,
                    end_time=new_end_time
                )
            
            # Save instance to database if one was created
            if (instance_type == "event_instance"):
                await updated_event_instances_repo.add(updated_instance, auto_commit=True)

            return Response(content="", status_code=HTTP_204_NO_CONTENT)

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
            start, timezone = validate_event_query_parameters(start, timezone)

            # Search for event instance
            start_time = convert_to_utc(timezone, start)
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