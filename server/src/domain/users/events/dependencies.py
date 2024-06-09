from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException
from uuid import UUID
from models.user import User
from models.event import Event
from domain.users.events.repositories import EventRepository, ExceptionDateRepository, UpdatedEventInstanceRepository

async def provide_events_repo(db_session: AsyncSession) -> EventRepository:
    """This provides the default Events repository"""
    return EventRepository(session=db_session)

async def provide_exception_dates_repo(db_session: AsyncSession) -> ExceptionDateRepository:
    """This provides the default ExceptionDates repository"""
    return ExceptionDateRepository(session=db_session)

async def provide_updated_event_instances_repo(db_session: AsyncSession) -> UpdatedEventInstanceRepository:
    """This provides the default UpdatedEventInstances repository"""
    return UpdatedEventInstanceRepository(session=db_session)

async def provide_event(user: User, event_id: str, events_repo: EventRepository) -> Event:
    """This provides the event belonging to the user identified by the event id"""
    # Check for valid uuid
    try:
        UUID(event_id)
    except ValueError:
        raise NotFoundException(detail="Event not found")

    # Get task by user id and event id
    event = await events_repo.get_one_or_none(user_id=user.id, id=event_id)
    if (event == None):
        raise NotFoundException(detail="Event not found")

    return event