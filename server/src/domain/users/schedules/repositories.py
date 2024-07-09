from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.schedule import Schedule
from uuid import UUID
from sqlalchemy import update

class ScheduleRepository(SQLAlchemyAsyncRepository[Schedule]):
    """Schedule repository"""

    model_type = Schedule

    async def mark_schedules_for_refresh(self, user_id: UUID) -> None:
        await self.session.execute(statement=update(Schedule).where(Schedule.user_id == user_id).values(requires_refresh = True))
        await self.session.commit()