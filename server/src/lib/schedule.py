from models.user import User
from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.preference import Preference
from models.habit import Habit, RepeatIntervalEnum
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.events.repositories import EventRepository
from domain.users.habits.repositories import HabitRepository
from lib.time import convert_to_utc
from lib.constraint import TimeBlock, schedule_daily_items
from datetime import time, datetime, timedelta
from pytz import timezone

# Time preference constants
MORNING = [(6 * 3600, 12 * 3600)]                   # 6am - 12pm
AFTERNOON = [(12 * 3600, 18 * 3600)]                # 12pm - 6pm
EVENING = [(18 * 3600, 21 * 3600)]                  # 6pm - 9pm
NIGHT = [(21 * 3600, 24 * 3600), (0, 6 * 3600)]     # 9pm - 6am

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

    async def schedule_events(self, user: User, events_repo: EventRepository, timezone_format: timezone) -> None:
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

    async def schedule_habits(self, user: User, habits_repo: HabitRepository) -> None:
        """Only schedules daily habits"""
        # Remove previous habit sessions
        self.schedule.schedule_items = [
            schedule_item for schedule_item in self.schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.HABIT
        ]

        # Get occupied timeblocks
        time_blocks = get_schedule_time_blocks(self.schedule)

        # Get habits
        habits = await habits_repo.list(user_id = user.id, repeat_interval = RepeatIntervalEnum.DAILY)

        # Preferred break length
        preferred_spacing = 3600 # Default one hour spacing for now

        # Get preferred times
        preferred_times = []
        for habit in habits:
            curr_preferred_times = []
            curr_preferred_times += MORNING if habit.morning_preferred else []
            curr_preferred_times += AFTERNOON if habit.afternoon_preferred else []
            curr_preferred_times += EVENING if habit.evening_preferred else []
            curr_preferred_times += NIGHT if habit.night_preferred else []

            preferred_times.append(curr_preferred_times)

        # Get habit sessions
        self.schedule.schedule_items += schedule_daily_items(
            time_blocks,
            [(habit.name, habit.duration * 60, ScheduleItemTypeEnum.HABIT) for habit in habits],
            preferred_times,
            preferred_spacing
        )

        self.schedule.requires_habit_refresh = False

    def schedule_work_sessions(self, preference: Preference) -> None:
        # Remove previous work sessions
        self.schedule.schedule_items = [
            schedule_item for schedule_item in self.schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.FOCUS_SESSION
        ]

        # Get occupied timeblocks
        time_blocks = get_schedule_time_blocks(self.schedule) + get_time_blocks(preference.end_of_work_day, preference.start_of_work_day)

        # Get best focus times and preferred break length
        best_focus_times = []
        preferred_break_length = 0
        if (preference != None):
            preferred_break_length = preference.break_length * 60
            for preferred_time_interval in reversed(preference.best_focus_times):
                best_focus_times += get_time_blocks(preferred_time_interval.start_time, preferred_time_interval.end_time)

        # Get work sessions
        self.schedule.schedule_items += schedule_daily_items(
            time_blocks,
            [("Work session", 3600, ScheduleItemTypeEnum.FOCUS_SESSION) for i in range(4)],
            [best_focus_times for i in range(4)],
            preferred_break_length
        )

        self.schedule.requires_work_refresh = False

class ScheduleDirector:

    async def generate_schedule(
        self,
        builder: ScheduleBuilder,
        user: User,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        timezone_format: timezone
    ) -> None:
        # Fetch preferences if needed
        preference = None
        if (builder.schedule.requires_sleep_refresh or builder.schedule.requires_work_refresh):
            preference = await preferences_repo.get_one_or_none(user_id = user.id)

        # Schedule sleep hours
        if (builder.schedule.requires_sleep_refresh):
            builder.schedule_sleep_hours(preference)

        # Schedule events
        if (builder.schedule.requires_event_refresh):
            await builder.schedule_events(user, events_repo, timezone_format)

        # Schedule habits
        if (builder.schedule.requires_habit_refresh):
            await builder.schedule_habits(user, habits_repo)

        # Schedule work sessions
        if (builder.schedule.requires_work_refresh):
            builder.schedule_work_sessions(preference)