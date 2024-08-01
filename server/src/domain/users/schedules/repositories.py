from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.user import User
from models.schedule import Schedule
from models.schedule_item import ScheduleItemTypeEnum
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.events.repositories import EventRepository
from domain.users.habits.repositories import HabitRepository
from lib.schedule import ScheduleBuilder, ScheduleDirector, WeeklyScheduleBuilder, WeeklyScheduleDirector
from uuid import UUID
from sqlalchemy import update, delete
from pytz import timezone
from datetime import date, timedelta

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

    async def refresh_schedule(self, user: User, schedule: Schedule, preferences_repo: PreferenceRepository, events_repo: EventRepository, habits_repo: HabitRepository, timezone_format: timezone) -> None:
        # Generate schedule
        schedule_builder = ScheduleBuilder(schedule)
        schedule_director = ScheduleDirector()
        await schedule_director.generate_schedule(schedule_builder, user, preferences_repo, events_repo, habits_repo, timezone_format)

        # Save schedule
        await self.update(schedule, auto_commit=True)

    async def create_weekly_schedule(self, user: User, schedule_date: date, preferences_repo: PreferenceRepository, events_repo: EventRepository, habits_repo: HabitRepository, timezone_format: timezone) -> list[Schedule]:
        # Get schedules
        schedules = await self.list(user_id=user.id)

        # If start of a new week remove the previous weekly schedule and create a new one
        if (schedule_date not in (schedule.date for schedule in schedules)):
            # Remove old schedule
            await self.session.execute(statement=delete(Schedule).where(Schedule.user_id == user.id))

            # Create schedules for each day of the week
            day_time_delta = timedelta(days=1)
            schedule_date_weekday = schedule_date.weekday()
            days = [schedule_date + (i - schedule_date_weekday) * day_time_delta for i in range(7)]
            schedules = [Schedule(user_id=user.id, date=day, requires_sleep_refresh=True, requires_event_refresh=True, requires_habit_refresh=True, requires_work_refresh=True) for day in days]

        # Generate weekly schedule
        schedule_builder = WeeklyScheduleBuilder(schedules)
        schedule_director = WeeklyScheduleDirector()
        await schedule_director.generate_schedule(schedule_builder, user, preferences_repo, events_repo, habits_repo, timezone_format)

        # Save schedules
        await self.upsert_many(schedules)

        return schedules