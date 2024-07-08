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
from lib.schedule import get_time_blocks
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
        # Fetch schedule if already generated
        schedule, created = await schedules_repo.get_or_create(user_id=user.id, date=schedule_date, auto_commit=True)
        if (not created):
            return schedule

        # Initialize variables
        time_blocks = []
        timezone_format = check_timezone(timezone)

        # Define session durations
        session_durations = [3600, 3600, 3600, 3600]

        # Get sleep schedule
        preferences = await preferences_repo.get_one_or_none(user_id = user.id)
        if (preferences != None and preferences.sleep_time != None and preferences.wake_up_time != None):
            time_blocks += get_time_blocks(preferences.sleep_time, preferences.wake_up_time)
            schedule.schedule_items += [ScheduleItem(
                name="Sleep",
                start_time=seconds_to_time_object(time_block[0]),
                end_time=seconds_to_time_object(time_block[1]),
                schedule_item_type=ScheduleItemTypeEnum.SLEEP,
                schedule_id=schedule.id
            ) for time_block in time_blocks]

        # Get events
        start_time = convert_to_utc(timezone_format, datetime(schedule_date.year, schedule_date.month, schedule_date.day))
        end_time = start_time + timedelta(days=1)
        start = start_time.timestamp()
        events = await events_repo.get_events_in_range(user.id, start_time, end_time, timezone_format)
        time_blocks += [(event.start_time.timestamp() - start, event.end_time.timestamp() - start) for event in events]
        schedule.schedule_items += [ScheduleItem(
            name=event.summary,
            start_time=seconds_to_time_object(event.start_time.timestamp() - start),
            end_time=seconds_to_time_object(event.end_time.timestamp() - start),
            schedule_item_type=ScheduleItemTypeEnum.EVENT,
            schedule_id=schedule.id
        ) for event in events]

        # Get best focus times
        best_focus_times = []
        for preferred_time_interval in reversed(preferences.best_focus_times):
            best_focus_times += get_time_blocks(preferred_time_interval.start_time, preferred_time_interval.end_time)

        # Get work sessions
        schedule.schedule_items += schedule_work_sessions(time_blocks, schedule.id, session_durations, best_focus_times, preferences.break_length * 60)

        # Save schedule items
        await schedules_repo.update(schedule, auto_commit=True)

        return schedule