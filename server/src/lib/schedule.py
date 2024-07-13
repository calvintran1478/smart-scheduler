from models.user import User
from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.preference import Preference
from domain.users.events.repositories import EventRepository
from lib.time import convert_to_utc
from lib.constraint import TimeBlock, schedule_work_sessions
from datetime import time, datetime, timedelta
from pytz import timezone

def get_time_blocks(start_time: time, end_time: time) -> list[TimeBlock]:
    # Get second timestamps of each time object from the start of the day
    start_timestamp = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_timestamp = end_time.hour * 3600 + end_time.minute * 60 + end_time.second

    # Add 1 or 2 timeblocks depending if the time interval crosses over midnight
    time_blocks = []
    if (start_timestamp > end_timestamp):
        time_blocks.append((start_timestamp, 24 * 3600))
        if (end_timestamp != 0):
            time_blocks.append((0, end_timestamp))
    else:
        time_blocks.append((start_timestamp, end_timestamp))

    return time_blocks

def get_time_obj_blocks(start_time: time, end_time: time) -> list[tuple[time, time]]:
    time_obj_blocks = []
    if (start_time > end_time):
        time_obj_blocks.append((start_time, time(23, 59, 59)))
        midnight = time()
        if (end_time != midnight):
            time_obj_blocks.append((midnight, end_time))
    else:
        time_obj_blocks.append((start_time, end_time))

    return time_obj_blocks

def get_schedule_time_blocks(schedule: Schedule) -> list[TimeBlock]:
    return [
        (schedule_item.start_time.hour * 3600 + schedule_item.start_time.minute * 60 + schedule_item.start_time.second,
        schedule_item.end_time.hour * 3600 + schedule_item.end_time.minute * 60 + schedule_item.end_time.second)
        for schedule_item in schedule.schedule_items
    ]

def requires_refresh(schedule: Schedule) -> bool:
    return schedule.requires_event_refresh or schedule.requires_habit_refresh \
        or schedule.requires_sleep_refresh or schedule.requires_work_refresh

class ScheduleBuilder:
    schedule: Schedule

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule

    def reset(self) -> None:
        self.schedule.schedule_items.clear()

    def schedule_sleep_hours(self, preference: Preference) -> None:
        # Remove previous sleep schedule
        self.schedule.schedule_items = [
            schedule_item for schedule_item in self.schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.SLEEP
        ]

        # Create new sleep schedule
        if (preference != None and preference.sleep_time != None and preference.wake_up_time != None):
            time_obj_blocks = get_time_obj_blocks(preference.sleep_time, preference.wake_up_time)
            self.schedule.schedule_items += [ScheduleItem(
                name="Sleep",
                start_time=time_obj_block[0],
                end_time=time_obj_block[1],
                schedule_item_type=ScheduleItemTypeEnum.SLEEP,
                schedule_id=self.schedule.id
            ) for time_obj_block in time_obj_blocks]

        self.schedule.requires_sleep_refresh = False

    async def schedule_events(self, user, events_repo: EventRepository, timezone_format: timezone) -> None:
        # Remove previous event items
        self.schedule.schedule_items = [
            schedule_item for schedule_item in self.schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.EVENT
        ]

        # Create new event items
        start_time = convert_to_utc(timezone_format, datetime(self.schedule.date.year, self.schedule.date.month, self.schedule.date.day))
        end_time = start_time + timedelta(days=1)
        events = await events_repo.get_events_in_range(user.id, start_time, end_time, timezone_format)
        self.schedule.schedule_items += [
            ScheduleItem(
                name=event.summary,
                start_time=time() if (event.start_time.date() < self.schedule.date) else event.start_time.time(),
                end_time=time(23, 59, 59) if (event.end_time.date() > self.schedule.date) else event.end_time.time(),
                schedule_item_type=ScheduleItemTypeEnum.EVENT,
            ) for event in events
        ]

        self.schedule.requires_event_refresh = False

    def schedule_habits(self) -> None:
        self.schedule.requires_habit_refresh = False

    def schedule_work_sessions(self, preference: Preference) -> None:
        # Remove previous work sessions
        self.schedule.schedule_items = [
            schedule_item for schedule_item in self.schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.FOCUS_SESSION
        ]

        # Get occupied timeblocks
        time_blocks = get_schedule_time_blocks(self.schedule)

        # Define session durations
        session_durations = [3600, 3600, 3600, 3600]

        # Get best focus times
        best_focus_times = []
        preferred_break_length = 0
        if (preference != None):
            preferred_break_length = preference.break_length * 60
            for preferred_time_interval in reversed(preference.best_focus_times):
                best_focus_times += get_time_blocks(preferred_time_interval.start_time, preferred_time_interval.end_time)

        # Get work sessions
        self.schedule.schedule_items += schedule_work_sessions(time_blocks, self.schedule.id, session_durations, best_focus_times, preferred_break_length)

        self.schedule.requires_work_refresh = False

class ScheduleDirector:

    async def generate_schedule(
        self,
        builder: ScheduleBuilder,
        user: User,
        preference: Preference,
        events_repo: EventRepository,
        timezone_format: timezone
    ) -> None:
        # Schedule sleep hours
        if (builder.schedule.requires_sleep_refresh):
            builder.schedule_sleep_hours(preference)

        # Schedule events
        if (builder.schedule.requires_event_refresh):
            await builder.schedule_events(user, events_repo, timezone_format)

        # Schedule habits
        if (builder.schedule.requires_habit_refresh):
            builder.schedule_habits()

        # Schedule work sessions
        if (builder.schedule.requires_work_refresh):
            builder.schedule_work_sessions(preference)