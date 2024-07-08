from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.schedules.repositories import ScheduleRepository

async def provide_schedules_repo(db_session: AsyncSession) -> ScheduleRepository:
    """This provides the default Schedules repository"""
    return ScheduleRepository(session=db_session)