from litestar import Controller, get
from litestar.di import Provide

from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.user import User
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo
from domain.users.schedules.dtos import ScheduleDTO
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.preferences.dependencies import provide_preferences_repo
from domain.users.events.repositories import EventRepository
from domain.users.events.dependencies import provide_events_repo
from domain.users.events.validators import check_timezone
from lib.time import convert_to_utc, seconds_to_time_object
from lib.schedule import requires_refresh, ScheduleBuilder, ScheduleDirector
from lib.constraint import schedule_work_sessions

from datetime import date, datetime, timedelta

class ScheduleController(Controller):
    dependencies = {
        "schedules_repo": Provide(provide_schedules_repo),
        "preferences_repo": Provide(provide_preferences_repo),
        "events_repo": Provide(provide_events_repo)
    }

    @get(path="/{schedule_date:date}", return_dto=ScheduleDTO)
    async def get_schedule(
        self,
        user: User,
        schedule_date: date,
        schedules_repo: ScheduleRepository,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        timezone: str
    ) -> Schedule:
        # Fetch schedule if already generated and does not require refresh
        schedule, created = await schedules_repo.get_or_create(user_id=user.id, date=schedule_date)
        if (not created and not requires_refresh(schedule)):
            return schedule

        # Initialize variables
        preferences = await preferences_repo.get_one_or_none(user_id = user.id)
        timezone_format = check_timezone(timezone)

        # Generate schedule
        scheduler_builder = ScheduleBuilder(schedule)
        schedule_director = ScheduleDirector()
        await schedule_director.generate_schedule(scheduler_builder, user, preferences, events_repo, timezone_format)

        # Save schedule items
        await schedules_repo.update(schedule, auto_commit=True)

        return schedule