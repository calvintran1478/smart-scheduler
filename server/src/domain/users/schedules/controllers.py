from litestar import Controller, post, get, patch
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException, NotFoundException
from litestar.di import Provide

from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.user import User
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo
from domain.users.schedules.schemas import CreateFocusSessionInput, UpdateScheduleItemInput
from domain.users.schedules.dtos import ScheduleDTO, ScheduleItemDTO
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.preferences.dependencies import provide_preferences_repo
from domain.users.events.repositories import EventRepository
from domain.users.events.dependencies import provide_events_repo
from domain.users.events.validators import check_timezone
from domain.users.habits.repositories import HabitRepository
from domain.users.habits.dependencies import provide_habits_repo
from lib.time import convert_to_utc, seconds_to_time_object
from lib.schedule import requires_refresh

from datetime import date
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
        # Check if the schedule has already been generated
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)

        # If not, plan out schedule for the week
        if (schedule == None):
            weekly_schedule = await schedules_repo.create_weekly_schedule(user, schedule_date, preferences_repo, events_repo, habits_repo, check_timezone(timezone))
            schedule = weekly_schedule[schedule_date.weekday()]

        # If yes, refresh the schedule if necessary
        elif (requires_refresh(schedule)):
            await schedules_repo.refresh_schedule(user, schedule, preferences_repo, events_repo, habits_repo, check_timezone(timezone))

        return schedule

    @post(path="/{schedule_date:date}/focus_sessions", return_dto=ScheduleItemDTO)
    async def create_focus_session(
        self,
        data: CreateFocusSessionInput,
        user: User,
        schedule_date: date,
        schedules_repo: ScheduleRepository,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        timezone: str
    ) -> ScheduleItem:
        # Get schedule
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None):
            weekly_schedule = await schedules_repo.create_weekly_schedule(user, schedule_date, preferences_repo, events_repo, habits_repo, check_timezone(timezone))
            schedule = weekly_schedule[schedule_date.weekday()]
        elif (requires_refresh(schedule)):
            await schedules_repo.refresh_schedule(user, schedule, preferences_repo, events_repo, habits_repo, check_timezone(timezone))

        # Check if chosen times overlap with existing schedule items
        if any(data.end_time > schedule_item.start_time and data.start_time < schedule_item.end_time for schedule_item in schedule.schedule_items):
            raise ClientException(detail="Chosen times must not overlap with existing schedule items", status_code=HTTP_409_CONFLICT)

        # Create focus session for the user
        focus_session = ScheduleItem(
            name=data.name,
            start_time=data.start_time,
            end_time=data.end_time,
            schedule_item_type=ScheduleItemTypeEnum.FOCUS_SESSION
        )

        schedule.schedule_items.append(focus_session)
        await schedules_repo.update(schedule, auto_commit=True)

        return focus_session

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