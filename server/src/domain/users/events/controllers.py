from litestar import Controller, post
from litestar.dto import DTOData
from litestar.di import Provide

from models.user import User
from models.event import Event
from domain.users.events.repositories import EventRepository
from domain.users.events.dependencies import provide_events_repo
from domain.users.events.dtos import CreateEventDTO, ReadEventDTO
from domain.users.events.validators import validate_event

class EventController(Controller):
    dependencies = {"events_repo": Provide(provide_events_repo)}

    @post(path="/", dto=CreateEventDTO, return_dto=ReadEventDTO)
    async def create_event(self, data: DTOData[Event], user: User, events_repo: EventRepository) -> Event:
        # Create event for the user
        event = data.create_instance(user_id = user.id)
        validate_event(event)
        await events_repo.add(event, auto_commit=True)

        return event