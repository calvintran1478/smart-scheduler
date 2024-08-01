from models.user import User
from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.preference import Preference
from models.habit import Habit, RepeatIntervalEnum
from models.event import Event
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.events.repositories import EventRepository
from domain.users.habits.repositories import HabitRepository
from lib.time import convert_to_utc
from lib.constraint import TimeBlock, schedule_daily_items, schedule_weekly_items
from datetime import time, date, datetime, timedelta
from pytz import timezone
from math import floor
from copy import deepcopy

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

def get_events_for_the_day(event_date: date, events: list[Event], timezone_format: timezone) -> list[Event]:
    event_date_start_time = convert_to_utc(timezone_format, datetime(event_date.year, event_date.month, event_date.day))
    event_date_end_time = event_date_start_time + timedelta(days=1)
    return [event for event in events if event.end_time > event_date_start_time and event.start_time < event_date_end_time]

def requires_refresh(schedule: Schedule, timezone: str) -> bool:
    timezone_change = (timezone != schedule.timezone)
    event_exists = any(schedule_item.schedule_item_type == ScheduleItemTypeEnum.EVENT for schedule_item in schedule.schedule_items)

    return schedule.requires_event_refresh or schedule.requires_habit_refresh \
        or schedule.requires_sleep_refresh or schedule.requires_work_refresh or (event_exists and timezone_change)

def get_weekly_preferred_times(daily_preferred_times: list[tuple[int, int]]) -> list[tuple[int, int]]:
    weekly_preferred_times = []
    for preferred_times in daily_preferred_times:
        weekly_preferred_times += [(preferred_times[0] + i * 86400, preferred_times[1] + i * 86400) for i in range(7)]
    return weekly_preferred_times

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

        # Declare timezone used for schedule
        self.schedule.timezone = str(timezone_format)
        self.schedule.requires_event_refresh = False

    def schedule_habits(self, daily_habits: list[Habit]) -> None:
        # Remove previous habit sessions
        self.schedule.schedule_items = [
            schedule_item for schedule_item in self.schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.HABIT
        ]

        # Get occupied timeblocks
        time_blocks = get_schedule_time_blocks(self.schedule)

        # Preferred break length
        preferred_spacing = 3600 # Default one hour spacing for now

        # Get preferred times
        preferred_times = []
        for habit in daily_habits:
            curr_preferred_times = []
            curr_preferred_times += MORNING if habit.morning_preferred else []
            curr_preferred_times += AFTERNOON if habit.afternoon_preferred else []
            curr_preferred_times += EVENING if habit.evening_preferred else []
            curr_preferred_times += NIGHT if habit.night_preferred else []

            preferred_times.append(curr_preferred_times)

        # Get habit sessions
        self.schedule.schedule_items += schedule_daily_items(
            time_blocks,
            [(habit.name, habit.duration * 60, ScheduleItemTypeEnum.HABIT) for habit in daily_habits],
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

class WeeklyScheduleBuilder:
    schedules: list[Schedule]

    def __init__(self, schedules: list[Schedule]) -> None:
        self.schedules = schedules

    def reset(self) -> None:
        for schedule in self.schedules:
            schedule.schedule_items.clear()

    def schedule_sleep_hours(self, preference: Preference) -> None:
        if (preference != None and preference.sleep_time != None and preference.wake_up_time != None):
            time_obj_blocks = get_time_obj_blocks(preference.sleep_time, preference.wake_up_time)
            sleep_schedule_items = [
                ScheduleItem(
                    name="Sleep",
                    start_time=time_obj_block[0],
                    end_time=time_obj_block[1],
                    schedule_item_type=ScheduleItemTypeEnum.SLEEP,
                ) for time_obj_block in time_obj_blocks
            ]

            for schedule in self.schedules:
                schedule.schedule_items += deepcopy(sleep_schedule_items)
                schedule.requires_sleep_refresh = False

    async def schedule_events(self, user: User, events_repo: EventRepository, timezone_format: timezone) -> None:
        # Get events for the week
        first_date = min(schedule.date for schedule in self.schedules)
        start_time = convert_to_utc(timezone_format, datetime(first_date.year, first_date.month, first_date.day))
        end_time = start_time + timedelta(days=7)
        events = await events_repo.get_events_in_range(user.id, start_time, end_time, timezone_format)

        # Add corresponding event items to each day
        for schedule in self.schedules:
            events_for_the_day = get_events_for_the_day(schedule.date, events, timezone_format)
            schedule.schedule_items += [
                ScheduleItem(
                    name=event.summary,
                    start_time=time() if (event.start_time.date() < schedule.date) else event.start_time.time(),
                    end_time=time(23, 59, 59) if (event.end_time.date() > schedule.date) else event.end_time.time(),
                    schedule_item_type=ScheduleItemTypeEnum.EVENT,
                ) for event in events_for_the_day
            ]

            # Declare timezone used for schedule
            schedule.timezone = str(timezone_format)
            schedule.requires_event_refresh = False

    def schedule_habits(self, habits: list[Habit]) -> None:
        daily_habits = [habit for habit in habits if habit.repeat_interval == RepeatIntervalEnum.DAILY]
        weekly_habits = [habit for habit in habits if habit.repeat_interval == RepeatIntervalEnum.WEEKLY]

        # Schedule daily habits
        schedule_builder = ScheduleBuilder(self.schedules[0])
        for schedule in self.schedules:
            schedule_builder.schedule = schedule
            schedule_builder.schedule_habits(daily_habits)

        # Schedule weekly habits
        num_weekly_habit_instances = sum(habit.frequency for habit in weekly_habits)
        if (num_weekly_habit_instances != 0):
            # Get occupied timeblocks
            schedule_time_blocks = [get_schedule_time_blocks(schedule) for schedule in self.schedules]
            for i, daily_time_blocks in enumerate(schedule_time_blocks):
                for j, (time_block_start, time_block_end) in enumerate(daily_time_blocks):
                    daily_time_blocks[j] = (time_block_start + i * 86400, time_block_end + i * 86400)
            time_blocks = sum(schedule_time_blocks, [])

            # Calculate preferred spacing
            preferred_spacing = floor(86400 * 7 / num_weekly_habit_instances)

            # Get preferred times
            preferred_times = []
            for habit in weekly_habits:
                curr_preferred_times = []
                curr_preferred_times += get_weekly_preferred_times(MORNING) if habit.morning_preferred else []
                curr_preferred_times += get_weekly_preferred_times(AFTERNOON) if habit.afternoon_preferred else []
                curr_preferred_times += get_weekly_preferred_times(EVENING) if habit.evening_preferred else []
                curr_preferred_times += get_weekly_preferred_times(NIGHT) if habit.night_preferred else []

                for _ in range(habit.frequency):
                    preferred_times.append(curr_preferred_times)

            # Get weekly habit instances
            weekly_items = []
            for habit in weekly_habits:
                weekly_items += [(habit.name, habit.duration * 60, ScheduleItemTypeEnum.HABIT)] * habit.frequency

            # Get habit sessions
            scheduled_weekly_habits = schedule_weekly_items(time_blocks, weekly_items, preferred_times, preferred_spacing)
            for i, schedule_items in enumerate(scheduled_weekly_habits):
                self.schedules[i].schedule_items += schedule_items

    def schedule_work_sessions(self, preference: Preference) -> None:
        schedule_builder = ScheduleBuilder(self.schedules[0])
        for schedule in self.schedules:
            schedule_builder.schedule = schedule
            schedule_builder.schedule_work_sessions(preference)

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
        # Check for timezone change
        timezone_change = (str(timezone_format) != builder.schedule.timezone)
        event_exists = any(schedule_item.schedule_item_type == ScheduleItemTypeEnum.EVENT for schedule_item in builder.schedule.schedule_items)
        if (event_exists and timezone_change):
            builder.schedule.requires_event_refresh = True
            builder.schedule.requires_habit_refresh = True
            builder.schedule.requires_work_refresh = True

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
            daily_habits = await habits_repo.list(user_id = user.id, repeat_interval = RepeatIntervalEnum.DAILY)
            builder.schedule_habits(daily_habits)

        # Schedule work sessions
        if (builder.schedule.requires_work_refresh):
            builder.schedule_work_sessions(preference)

class WeeklyScheduleDirector:

    async def generate_schedule(
        self,
        builder: WeeklyScheduleBuilder,
        user: User,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        timezone_format: timezone
    ) -> None:
        # Fetch necessary info for creating the schedule
        preference = await preferences_repo.get_one_or_none(user_id = user.id)
        habits = await habits_repo.list(user_id = user.id)

        # Create weekly schedule
        builder.reset()
        builder.schedule_sleep_hours(preference)
        await builder.schedule_events(user, events_repo, timezone_format)
        builder.schedule_habits(habits)
        builder.schedule_work_sessions(preference)