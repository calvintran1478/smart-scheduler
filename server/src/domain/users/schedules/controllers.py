from litestar import Controller, get, patch
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException, NotFoundException
from litestar.di import Provide

from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.user import User
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo
from domain.users.schedules.schemas import UpdateScheduleItemInput
from domain.users.schedules.dtos import ScheduleDTO
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.preferences.dependencies import provide_preferences_repo
from domain.users.events.repositories import EventRepository
from domain.users.events.dependencies import provide_events_repo
from domain.users.events.validators import check_timezone
from domain.users.habits.repositories import HabitRepository
from domain.users.habits.dependencies import provide_habits_repo
from lib.time import convert_to_utc, seconds_to_time_object
from lib.schedule import requires_refresh, ScheduleBuilder, ScheduleDirector, WeeklyScheduleBuilder, WeeklyScheduleDirector

from datetime import date, datetime, timedelta
from uuid import UUID

class ScheduleController(Controller):
    dependencies = {
        "schedules_repo": Provide(provide_schedules_repo),
        "preferences_repo": Provide(provide_preferences_repo),
        "events_repo": Provide(provide_events_repo),
        "habits_repo": Provide(provide_habits_repo)
    }

    @get(path="/{schedule_date:date}", return_dto=ScheduleDTO)
    async def get_schedule(
        self,
        user: User,
        schedule_date: date,
        schedules_repo: ScheduleRepository,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        timezone: str
    ) -> Schedule:
        # Fetch schedule if already generated and does not require refresh
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule != None and not requires_refresh(schedule)):
            return schedule

        # Start new week
        if (schedule == None):
            # Create schedules for each day of the week
            day_time_delta = timedelta(days=1)
            schedule_date_weekday = schedule_date.weekday()
            days = [schedule_date + (i - schedule_date_weekday) * day_time_delta for i in range(7)]
            schedules = [Schedule(user_id=user.id, date=day) for day in days]

            # Generate weekly schedule
            schedule_builder = WeeklyScheduleBuilder(schedules)
            schedule_director = WeeklyScheduleDirector()
            await schedule_director.generate_schedule(schedule_builder, user, preferences_repo, events_repo, habits_repo, check_timezone(timezone))

            # Save schedules
            schedule = schedules[schedule_date_weekday]
            await schedules_repo.add_many(schedules)

        # Update schedule from the current week
        else:
            # Generate schedule
            schedule_builder = ScheduleBuilder(schedule)
            schedule_director = ScheduleDirector()
            await schedule_director.generate_schedule(schedule_builder, user, preferences_repo, events_repo, habits_repo, check_timezone(timezone))

            # Save schedule
            await schedules_repo.update(schedule, auto_commit=True)

        return schedule

    @patch(path="/{schedule_date:date}/schedule_items/{schedule_item_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def update_schedule_item(self, data: UpdateScheduleItemInput, user: User, schedule_date: date, schedule_item_id: UUID, schedules_repo: ScheduleRepository) -> None:
        # Search for schedule item
        selected_schedule_item = None
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None):
            raise NotFoundException(detail="Schedule item not found")

        try:
            selected_schedule_item = next(schedule_item for schedule_item in schedule.schedule_items if schedule_item.id == schedule_item_id)
        except StopIteration:
            raise NotFoundException(detail="Schedule item not found")

        # Check if this schedule item can be modified
        if (selected_schedule_item.schedule_item_type in [ScheduleItemTypeEnum.SLEEP, ScheduleItemTypeEnum.EVENT]):
            raise ClientException(detail="Schedule item must be a habit session or work session")

        # Update time values
        if (data.start_time != None):
            selected_schedule_item.start_time = data.start_time

        if (data.end_time != None):
            selected_schedule_item.end_time = data.end_time

        # Check if new time values are valid
        if (selected_schedule_item.start_time > selected_schedule_item.end_time):
            raise ClientException(detail="Start time must come before end time")

        if any(selected_schedule_item.end_time > schedule_item.start_time and selected_schedule_item.start_time < schedule_item.end_time \
            for schedule_item in schedule.schedule_items if schedule_item.id != selected_schedule_item.id):
                raise ClientException(detail="New times must not overlap with existing schedule items", status_code=HTTP_409_CONFLICT)

        await schedules_repo.update(schedule, auto_commit=True)