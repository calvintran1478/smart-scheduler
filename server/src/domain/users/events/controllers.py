from litestar import Controller, Response, post, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.dto import DTOData
from litestar.di import Provide

from models.user import User
from models.event import Event
from domain.users.events.repositories import EventRepository
from domain.users.events.dependencies import provide_events_repo, provide_event
from domain.users.events.dtos import CreateEventDTO, UpdateEventDTO, ReadEventDTO
from domain.users.events.validators import validate_event

class EventController(Controller):
    dependencies = {"events_repo": Provide(provide_events_repo), "event": Provide(provide_event)}

    @post(path="/", dto=CreateEventDTO, return_dto=ReadEventDTO)
    async def create_event(self, data: DTOData[Event], user: User, events_repo: EventRepository) -> Event:
        # Create event for the user
        event = data.create_instance(user_id = user.id)
        validate_event(event)
        await events_repo.add(event, auto_commit=True)

        return event

    @patch(path="/{event_id:str}", dto=UpdateEventDTO)
    async def update_event(self, data: DTOData[Event], event: Event) -> None:
        # Update event
        data.update_instance(event)
        validate_event(event)

        return Response(content="", status_code=HTTP_204_NO_CONTENT)

    @delete(path="/{event_id:str}")
    async def remove_event(self, event: Event, events_repo: EventRepository) -> None:
        await events_repo.delete(event.id)