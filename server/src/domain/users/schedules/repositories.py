from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.schedule import Schedule
from models.schedule_item import ScheduleItemTypeEnum
from uuid import UUID
from sqlalchemy import update

class ScheduleRepository(SQLAlchemyAsyncRepository[Schedule]):
    """Schedule repository"""

    model_type = Schedule

    async def mark_schedules_for_refresh(self, user_id: UUID, schedule_item_types: list[ScheduleItemTypeEnum]) -> None:
        for schedule_item_type in schedule_item_types:
            match schedule_item_type:
                case ScheduleItemTypeEnum.EVENT:
                    await self.session.execute(statement=update(Schedule).where(Schedule.user_id == user_id).values(requires_event_refresh = True))
                case ScheduleItemTypeEnum.HABIT:
                    await self.session.execute(statement=update(Schedule).where(Schedule.user_id == user_id).values(requires_habit_refresh = True))
                case ScheduleItemTypeEnum.SLEEP:
                    await self.session.execute(statement=update(Schedule).where(Schedule.user_id == user_id).values(requires_sleep_refresh = True))
                case ScheduleItemTypeEnum.FOCUS_SESSION:
                    await self.session.execute(statement=update(Schedule).where(Schedule.user_id == user_id).values(requires_work_refresh = True))
        await self.session.commit()