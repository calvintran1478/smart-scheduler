from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.events.repositories import EventRepository

async def provide_events_repo(db_session: AsyncSession) -> EventRepository:
    """This provides the default Events repository"""
    return EventRepository(session=db_session)