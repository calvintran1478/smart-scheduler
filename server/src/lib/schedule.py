from models.user import User
from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.preference import Preference
from models.habit import Habit, RepeatIntervalEnum
from models.event import Event
from models.task import Task
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.events.repositories import EventRepository
from domain.users.habits.repositories import HabitRepository
from domain.users.tasks.repositories import TaskRepository
from lib.time import convert_to_utc, get_time_difference, seconds_to_time_object, get_time_blocks, get_time_obj_blocks, get_schedule_time_blocks, SECONDS_PER_DAY, DAYS_PER_WEEK, START_OF_DAY, END_OF_DAY
from lib.constraint import schedule_daily_items, schedule_weekly_items
from lib.strategy import WorkStrategy, ChipStrategy
from datetime import date, datetime, timedelta, time
from pytz import timezone
from math import floor
from copy import deepcopy
from collections.abc import Sequence
from typing import Optional

import pytz

type ScheduleItemDetails = tuple[str, int, ScheduleItemTypeEnum, bool]

# Helper function for creating time constants
def get_weekly_preferred_times(daily_preferred_times: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    weekly_preferred_times = []
    for preferred_times in daily_preferred_times:
        weekly_preferred_times += [(preferred_times[0] + i * SECONDS_PER_DAY, preferred_times[1] + i * SECONDS_PER_DAY) for i in range(DAYS_PER_WEEK)]
    return weekly_preferred_times

# Time preference constants
MORNING = [(6 * 3600, 12 * 3600)]                   # 6am - 12pm
AFTERNOON = [(12 * 3600, 18 * 3600)]                # 12pm - 6pm
EVENING = [(18 * 3600, 21 * 3600)]                  # 6pm - 9pm
NIGHT = [(21 * 3600, 24 * 3600), (0, 6 * 3600)]     # 9pm - 6am

WEEKLY_MORNING = get_weekly_preferred_times(MORNING)
WEEKLY_AFTERNOON = get_weekly_preferred_times(AFTERNOON)
WEEKLY_EVENING = get_weekly_preferred_times(EVENING)
WEEKLY_NIGHT = get_weekly_preferred_times(NIGHT)

def get_events_for_the_day(event_date: date, events: Sequence[Event], timezone_format: timezone) -> tuple[Event, ...]:
    event_date_start_time = convert_to_utc(timezone_format, datetime(event_date.year, event_date.month, event_date.day))
    event_date_end_time = event_date_start_time + timedelta(days=1)
    return tuple(event for event in events if event.end_time > event_date_start_time and event.start_time < event_date_end_time)

def requires_refresh(schedule: Schedule, timezone_str: str) -> bool:
    timezone_change = (timezone_str != schedule.timezone)
    event_exists = any(schedule_item.schedule_item_type == ScheduleItemTypeEnum.EVENT for schedule_item in schedule.schedule_items)

    return schedule.requires_event_refresh or schedule.requires_habit_refresh \
        or schedule.requires_sleep_refresh or schedule.requires_work_refresh or (event_exists and timezone_change)

async def requires_week_refresh(schedule: Schedule, timezone_str: str, user: User, habits_repo: HabitRepository) -> bool:
    timezone_change = (timezone_str != schedule.timezone)
    event_exists = any(schedule_item.schedule_item_type == ScheduleItemTypeEnum.EVENT for schedule_item in schedule.schedule_items)

    return (schedule.requires_habit_refresh or (event_exists and timezone_change)) \
        and (await habits_repo.exists(user_id=user.id, repeat_interval=RepeatIntervalEnum.WEEKLY))

def remove_schedule_items_by_type(schedule: Schedule, schedule_item_type: ScheduleItemTypeEnum, names: Optional[Sequence[str]] = None) -> tuple[tuple[ScheduleItem, ...], tuple[ScheduleItem, ...]]:
    # Keep track of schedule items to be removed
    locked_schedule_items = tuple(
        schedule_item for schedule_item in schedule.schedule_items
        if schedule_item.schedule_item_type == schedule_item_type and schedule_item.locked and (names == None or schedule_item.name in names)
    )
    non_locked_schedule_items = tuple(
        schedule_item for schedule_item in schedule.schedule_items
        if schedule_item.schedule_item_type == schedule_item_type and not schedule_item.locked and (names == None or schedule_item.name in names)
    )

    # Remove schedule items from schedule
    schedule.schedule_items = [
        schedule_item for schedule_item in schedule.schedule_items
        if schedule_item.schedule_item_type != schedule_item_type or (names != None and schedule_item.name not in names)
    ]

    return locked_schedule_items, non_locked_schedule_items

def get_previous_daily_items(locked_schedule_items: Sequence[ScheduleItem], non_locked_schedule_items: Sequence[ScheduleItem]) -> list[ScheduleItemDetails]:
    return [(schedule_item.name, get_time_difference(schedule_item.start_time, schedule_item.end_time), schedule_item.schedule_item_type, True, schedule_item.ref_id) for schedule_item in locked_schedule_items] + \
        [(schedule_item.name, get_time_difference(schedule_item.start_time, schedule_item.end_time), schedule_item.schedule_item_type, False, schedule_item.ref_id) for schedule_item in non_locked_schedule_items]

def remove_weekly_habit_sessions(schedules: Sequence[Schedule], weekly_habit_names: Sequence[str]) -> tuple[list[tuple[ScheduleItem, ...]], list[tuple[ScheduleItem, ...]]]:
    locked_schedule_items = []
    non_locked_schedule_items = []

    for schedule in schedules:
        # Keep track of schedules to remove
        weekly_habit_sessions = tuple(
            schedule_item for schedule_item in schedule.schedule_items
            if schedule_item.schedule_item_type == ScheduleItemTypeEnum.HABIT and schedule_item.name in weekly_habit_names
        )

        locked_schedule_items.append(
            tuple(schedule_item for schedule_item in weekly_habit_sessions if schedule_item.locked)
        )

        non_locked_schedule_items.append(
            tuple(schedule_item for schedule_item in weekly_habit_sessions if not schedule_item.locked)
        )

        # Remove weekly habit sessions from schedule
        schedule.schedule_items = [
            schedule_item for schedule_item in schedule.schedule_items
            if schedule_item.schedule_item_type != ScheduleItemTypeEnum.HABIT or schedule_item.name not in weekly_habit_names
        ]

    return locked_schedule_items, non_locked_schedule_items

class TimeDistributionPlanner:
    strategy: WorkStrategy

    def __init__(self, strategy: WorkStrategy) -> None:
        self.strategy = strategy
    
    def distribute_work_hours(self, schedules_to_plan: Sequence[Schedule], tasks: Sequence[Task], preference: Preference, start_time: time, timezone: pytz.timezone) -> None:
        work_plan = self.strategy.execute(schedules_to_plan, tasks, preference, start_time, timezone)

        for schedule in schedules_to_plan:
            for assigned_focus_block in work_plan[schedule]:
                assigned_task = next(task for task in tasks if task.id == assigned_focus_block[0])
                focus_session = ScheduleItem(
                    name=assigned_task.name,
                    start_time=START_OF_DAY,
                    end_time=seconds_to_time_object(assigned_focus_block[1]),
                    locked=False,
                    schedule_item_type=ScheduleItemTypeEnum.FOCUS_SESSION,
                    ref_id=assigned_task.id
                )
                schedule.schedule_items.append(focus_session)
                schedule.requires_work_refresh = True

class ScheduleBuilder:
    schedule: Schedule

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule

    def reset(self) -> None:
        self.schedule.schedule_items.clear()

    def schedule_sleep_hours(self, preference: Optional[Preference] = None) -> None:
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
                schedule_item_type=ScheduleItemTypeEnum.SLEEP
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
                start_time=START_OF_DAY if (event.start_time.date() < self.schedule.date) else event.start_time.time(),
                end_time=END_OF_DAY if (event.end_time.date() > self.schedule.date) else event.end_time.time(),
                schedule_item_type=ScheduleItemTypeEnum.EVENT,
                ref_id=event.id
            ) for event in events
        ]

        # Declare timezone used for schedule
        self.schedule.timezone = str(timezone_format)
        self.schedule.requires_event_refresh = False

    def schedule_habits(self, daily_habits: Sequence[Habit]) -> None:
        # Remove previous habit sessions
        daily_habit_names = tuple(habit.name for habit in daily_habits)
        locked_habit_sessions, non_locked_habit_sessions = remove_schedule_items_by_type(self.schedule, ScheduleItemTypeEnum.HABIT, daily_habit_names)

        # Get daily habit instances
        daily_items = get_previous_daily_items(locked_habit_sessions, non_locked_habit_sessions)

        # Add missing habit sessions
        for habit in daily_habits:
            num_habit_instances = sum((1 if daily_item[0] == habit.name else 0) for daily_item in daily_items)
            num_habit_instances_to_add = max(0, habit.frequency - num_habit_instances)
            daily_items += [(habit.name, habit.duration * 60, ScheduleItemTypeEnum.HABIT, False, None)] * num_habit_instances_to_add

        # Get preferred times
        preferred_times = []
        for i, daily_item in enumerate(daily_items):
            habit = next(habit for habit in daily_habits if habit.name == daily_item[0])
            curr_preferred_times = get_time_blocks(locked_habit_sessions[i].start_time, locked_habit_sessions[i].end_time) if (i < len(locked_habit_sessions)) else []
            curr_preferred_times += MORNING if habit.morning_preferred else []
            curr_preferred_times += AFTERNOON if habit.afternoon_preferred else []
            curr_preferred_times += EVENING if habit.evening_preferred else []
            curr_preferred_times += NIGHT if habit.night_preferred else []

            preferred_times.append(curr_preferred_times)

        # Get occupied timeblocks
        schedule_time_blocks = get_schedule_time_blocks(self.schedule)
        time_blocks = tuple(schedule_time_blocks for _ in range(len(daily_items)))

        # Preferred break length
        preferred_spacing = 3600 # Default one hour spacing for now

        # Get habit sessions
        self.schedule.schedule_items += schedule_daily_items(time_blocks, daily_items, preferred_times, preferred_spacing)

        self.schedule.requires_habit_refresh = False

    def schedule_work_sessions(self, tasks: list[Task], preference: Optional[Preference] = None) -> None:
        # Remove previous work sessions
        locked_focus_sessions, non_locked_focus_sessions = remove_schedule_items_by_type(self.schedule, ScheduleItemTypeEnum.FOCUS_SESSION)

        # Get daily items
        daily_items = get_previous_daily_items(locked_focus_sessions, non_locked_focus_sessions)

        # Get default best focus times based on preference
        default_best_focus_times = []
        if (preference != None):
            for preferred_time_interval in reversed(preference.best_focus_times):
                default_best_focus_times += get_time_blocks(preferred_time_interval.start_time, preferred_time_interval.end_time)

        # Prioritize previous user chosen values
        locked_best_focus_times = [
            get_time_blocks(focus_session.start_time, focus_session.end_time) + default_best_focus_times
            for focus_session in locked_focus_sessions
        ]

        non_locked_best_focus_times = [default_best_focus_times] * len(non_locked_focus_sessions)
        best_focus_times = locked_best_focus_times + non_locked_best_focus_times

        # Get occupied timeblocks
        schedule_time_blocks = get_schedule_time_blocks(self.schedule) + (get_time_blocks(preference.end_of_work_day, preference.start_of_work_day) if (preference != None) else [])
        time_blocks = [schedule_time_blocks for _ in range(len(daily_items))]
        for i, daily_item in enumerate(daily_items):
            try:
                item_task = next(task for task in tasks if task.id == daily_item[4])
                if (self.schedule.date == item_task.deadline.date()):
                    time_blocks[i] = time_blocks[i] + [(item_task.deadline.hour * 3600 + item_task.deadline.minute * 60 + item_task.deadline.second, SECONDS_PER_DAY)]
            except StopIteration:
                pass

        # Preferred break length
        preferred_break_length = preference.break_length * 60 if (preference != None) else 0

        # Get work sessions
        self.schedule.schedule_items += schedule_daily_items(time_blocks, daily_items, best_focus_times, preferred_break_length)

        self.schedule.requires_work_refresh = False

    def add_work_session(self, name: str, duration: int, preference: Optional[Preference] = None) -> ScheduleItem:
        # Get occupied time blocks
        time_blocks = get_schedule_time_blocks(self.schedule) + (get_time_blocks(preference.end_of_work_day, preference.start_of_work_day) if (preference != None) else [])

        # Daily items
        daily_items = ((name, duration, ScheduleItemTypeEnum.FOCUS_SESSION, False, None),)

        # Best focus times
        best_focus_times = []
        if (preference != None):
            for preferred_time_interval in reversed(preference.best_focus_times):
                best_focus_times += get_time_blocks(preferred_time_interval.start_time, preferred_time_interval.end_time)

        # Preferred break length
        preferred_break_length = 0

        # Schedule focus session
        focus_session = schedule_daily_items((time_blocks,), daily_items, (best_focus_times,), preferred_break_length)[0]
        self.schedule.schedule_items.append(focus_session)

        return focus_session

    def add_habit_session(self, habit: Habit) -> ScheduleItem:
        # Get occupied time blocks
        time_blocks = get_schedule_time_blocks(self.schedule)

        # Daily items
        daily_items = ((habit.name, habit.duration * 60, ScheduleItemTypeEnum.HABIT, False, None),)

        # Preferred times
        preferred_times = []
        preferred_times += MORNING if habit.morning_preferred else []
        preferred_times += AFTERNOON if habit.afternoon_preferred else []
        preferred_times += EVENING if habit.evening_preferred else []
        preferred_times += NIGHT if habit.night_preferred else []

        # Preferred break length
        preferred_spacing = 0

        # Schedule habit session
        habit_session = schedule_daily_items((time_blocks,), daily_items, (preferred_times,), preferred_spacing)[0]
        self.schedule.schedule_items.append(habit_session)

        return habit_session

class WeeklyScheduleBuilder:
    schedules: Sequence[Schedule]

    def __init__(self, schedules: Sequence[Schedule]) -> None:
        self.schedules = schedules

    def reset(self) -> None:
        for schedule in self.schedules:
            schedule.schedule_items.clear()

    def schedule_sleep_hours(self, preference: Optional[Preference] = None) -> None:
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
                if (schedule.requires_sleep_refresh):
                    # Remove previous sleep hours
                    schedule.schedule_items = [
                        schedule_item for schedule_item in schedule.schedule_items
                        if schedule_item.schedule_item_type != ScheduleItemTypeEnum.SLEEP
                    ]

                    # Add new sleep hours
                    schedule.schedule_items += deepcopy(sleep_schedule_items)
                    schedule.requires_sleep_refresh = False

    async def schedule_events(self, user: User, events_repo: EventRepository, timezone_format: timezone) -> None:
        # Get events for the week
        first_date = min(schedule.date for schedule in self.schedules)
        start_time = convert_to_utc(timezone_format, datetime(first_date.year, first_date.month, first_date.day))
        end_time = start_time + timedelta(days=DAYS_PER_WEEK)
        events = await events_repo.get_events_in_range(user.id, start_time, end_time, timezone_format)

        # Add corresponding event items to each day
        for schedule in self.schedules:
            if (schedule.requires_event_refresh):
                # Remove previous event items
                schedule.schedule_items = [
                    schedule_item for schedule_item in schedule.schedule_items
                    if schedule_item.schedule_item_type != ScheduleItemTypeEnum.EVENT
                ]

                # Add new event items
                events_for_the_day = get_events_for_the_day(schedule.date, events, timezone_format)
                schedule.schedule_items += [
                    ScheduleItem(
                        name=event.summary,
                        start_time=START_OF_DAY if (event.start_time.date() < schedule.date) else event.start_time.time(),
                        end_time=END_OF_DAY if (event.end_time.date() > schedule.date) else event.end_time.time(),
                        schedule_item_type=ScheduleItemTypeEnum.EVENT,
                        ref_id=event.id
                    ) for event in events_for_the_day
                ]

                # Declare timezone used for schedule
                schedule.timezone = str(timezone_format)
                schedule.requires_event_refresh = False

    def schedule_habits(self, habits: Sequence[Habit]) -> None:
        daily_habits = tuple(habit for habit in habits if habit.repeat_interval == RepeatIntervalEnum.DAILY)
        weekly_habits = tuple(habit for habit in habits if habit.repeat_interval == RepeatIntervalEnum.WEEKLY)

        # Schedule daily habits
        schedule_builder = ScheduleBuilder(self.schedules[0])
        for schedule in self.schedules:
            if (schedule.requires_habit_refresh):
                schedule_builder.schedule = schedule
                schedule_builder.schedule_habits(daily_habits)

        # Schedule weekly habits
        num_weekly_habit_instances = sum(habit.frequency for habit in weekly_habits)
        if (num_weekly_habit_instances != 0):
            # Remove previous weekly habit sessions
            weekly_habit_names = tuple(habit.name for habit in weekly_habits)
            locked_weekly_habit_sessions, non_locked_weekly_habit_sessions = remove_weekly_habit_sessions(self.schedules, weekly_habit_names)

            # Get weekly habit instances
            locked_weekly_items = {}
            non_locked_weekly_items = {}
            for i in range(DAYS_PER_WEEK):
                locked_weekly_items[i] = [(schedule_item.name, get_time_difference(schedule_item.start_time, schedule_item.end_time), schedule_item.schedule_item_type, True, None) for schedule_item in locked_weekly_habit_sessions[i]]
                non_locked_weekly_items[i] = [(schedule_item.name, get_time_difference(schedule_item.start_time, schedule_item.end_time), schedule_item.schedule_item_type, False, None) for schedule_item in non_locked_weekly_habit_sessions[i]]
            weekly_items = sum(locked_weekly_items.values(), []) + sum(non_locked_weekly_items.values(), [])

            # Add missing habit sessions
            for habit in weekly_habits:
                num_habit_instances = sum((1 if weekly_item[0] == habit.name else 0) for weekly_item in weekly_items)
                num_habit_instances_to_add = max(0, habit.frequency - num_habit_instances)
                weekly_items += [(habit.name, habit.duration * 60, ScheduleItemTypeEnum.HABIT, False, None)] * num_habit_instances_to_add

            # Get number of locked items
            num_locked_weekly_items = sum((1 if weekly_item[3] else 0) for weekly_item in weekly_items)

            # Get preferred times
            preferred_times = []

            # Prioritize previous user chosen values
            for i, locked_habit_sessions in enumerate(locked_weekly_habit_sessions):
                for habit_session in locked_habit_sessions:
                    habit = next(habit for habit in weekly_habits if habit.name == habit_session.name)
                    curr_preferred_times = get_time_blocks(habit_session.start_time, habit_session.end_time)
                    for j, (time_block_start, time_block_end) in enumerate(curr_preferred_times):
                        curr_preferred_times[j] = (time_block_start + i * SECONDS_PER_DAY, time_block_end + i * SECONDS_PER_DAY)

                    curr_preferred_times += WEEKLY_MORNING if habit.morning_preferred else []
                    curr_preferred_times += WEEKLY_AFTERNOON if habit.afternoon_preferred else []
                    curr_preferred_times += WEEKLY_EVENING if habit.evening_preferred else []
                    curr_preferred_times += WEEKLY_NIGHT if habit.night_preferred else []

                    preferred_times.append(curr_preferred_times)

            for i, weekly_item in enumerate(weekly_items[num_locked_weekly_items:]):
                habit = next(habit for habit in weekly_habits if habit.name == weekly_item[0])
                curr_preferred_times = []
                curr_preferred_times += WEEKLY_MORNING if habit.morning_preferred else []
                curr_preferred_times += WEEKLY_AFTERNOON if habit.afternoon_preferred else []
                curr_preferred_times += WEEKLY_EVENING if habit.evening_preferred else []
                curr_preferred_times += WEEKLY_NIGHT if habit.night_preferred else []

                preferred_times.append(curr_preferred_times)

            # Get occupied timeblocks
            schedule_time_blocks = tuple(get_schedule_time_blocks(schedule) for schedule in self.schedules)
            for i, daily_time_blocks in enumerate(schedule_time_blocks):
                for j, (time_block_start, time_block_end) in enumerate(daily_time_blocks):
                    daily_time_blocks[j] = (time_block_start + i * SECONDS_PER_DAY, time_block_end + i * SECONDS_PER_DAY)
            weekly_schedule_time_blocks = sum(schedule_time_blocks, [])
            time_blocks = tuple(weekly_schedule_time_blocks for _ in range(len(weekly_items)))

            # Calculate preferred spacing
            preferred_spacing = floor(SECONDS_PER_DAY * DAYS_PER_WEEK / num_weekly_habit_instances)

            # Get habit sessions
            scheduled_weekly_habits = schedule_weekly_items(time_blocks, weekly_items, preferred_times, preferred_spacing)
            for i, schedule_items in enumerate(scheduled_weekly_habits):
                self.schedules[i].schedule_items += schedule_items

    def schedule_work_sessions(self, schedule_date: date, timezone_format: timezone, tasks: list[Task], preference: Optional[Preference] = None) -> None:
        schedule_to_refresh = next(schedule for schedule in self.schedules if schedule.date == schedule_date)
        if (schedule_to_refresh.requires_work_refresh):
            schedule_builder = ScheduleBuilder(schedule_to_refresh)
            schedule_builder.schedule_work_sessions(tasks, preference)

class ScheduleDirector:

    async def generate_schedule(
        self,
        builder: ScheduleBuilder,
        user: User,
        schedules: Sequence[Schedule],
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        tasks_repo: TaskRepository,
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
            preference = await preferences_repo.get_one_or_none(user_id = user.id, auto_expunge=True)

        # Clear previously planned focus sessions
        if (builder.schedule.requires_work_refresh):
            for schedule in schedules:
                schedule.schedule_items = [schedule_item for schedule_item in schedule.schedule_items if schedule_item.schedule_item_type != ScheduleItemTypeEnum.FOCUS_SESSION]

        # Schedule sleep hours
        if (builder.schedule.requires_sleep_refresh):
            builder.schedule_sleep_hours(preference)

        # Schedule events
        if (builder.schedule.requires_event_refresh):
            await builder.schedule_events(user, events_repo, timezone_format)

        # Schedule habits
        if (builder.schedule.requires_habit_refresh):
            daily_habits = await habits_repo.list(user_id = user.id, repeat_interval = RepeatIntervalEnum.DAILY, auto_expunge=True)
            builder.schedule_habits(daily_habits)

        # Schedule work sessions
        if (builder.schedule.requires_work_refresh):
            # Fetch tasks
            tasks = await tasks_repo.list(user_id = user.id, done = False, auto_expunge=True)

            # Determine distribution of focus sessions based on some work strategy
            strategy = ChipStrategy()
            time_planner = TimeDistributionPlanner(strategy)
            time_planner.distribute_work_hours(schedules, tasks, preference, START_OF_DAY, timezone_format)

            builder.schedule_work_sessions(tasks, preference)

class WeeklyScheduleDirector:

    async def generate_schedule(
        self,
        builder: WeeklyScheduleBuilder,
        user: User,
        schedule_date: date,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        tasks_repo: TaskRepository,
        timezone_format: timezone
    ) -> None:
        # Check for timezone change
        timezone_str = str(timezone_format)
        for schedule in builder.schedules:
            timezone_change = timezone_str != schedule.timezone
            event_exists = any(schedule_item.schedule_item_type == ScheduleItemTypeEnum.EVENT for schedule_item in schedule.schedule_items)
            if (event_exists and timezone_change):
                schedule.requires_event_refresh = True
                schedule.requires_habit_refresh = True
                schedule.requires_work_refresh = True

        # Fetch preferences if needed
        preference = None
        if any(schedule.requires_sleep_refresh or schedule.requires_work_refresh for schedule in builder.schedules):
            preference = await preferences_repo.get_one_or_none(user_id = user.id, auto_expunge=True)

        # Get schedules for remaining days of the week
        schedules_to_plan = tuple(schedule for schedule in builder.schedules if schedule.date >= schedule_date)

        # Clear previously planned focus sessions
        if any(schedule.requires_work_refresh for schedule in schedules_to_plan):
            for schedule in schedules_to_plan:
                schedule.schedule_items = [schedule_item for schedule_item in schedule.schedule_items if schedule_item.schedule_item_type != ScheduleItemTypeEnum.FOCUS_SESSION]

        # Schedule sleep hours
        if any(schedule.requires_sleep_refresh for schedule in builder.schedules):
            builder.schedule_sleep_hours(preference)

        # Schedule events
        if any(schedule.requires_event_refresh for schedule in builder.schedules):
            await builder.schedule_events(user, events_repo, timezone_format)

        # Schedule habits
        if any(schedule.requires_habit_refresh for schedule in builder.schedules):
            habits = await habits_repo.list(user_id = user.id, auto_expunge=True)
            builder.schedule_habits(habits)

        # Schedule work sessions
        if any(schedule.requires_work_refresh for schedule in schedules_to_plan):
            # Fetch tasks
            tasks = await tasks_repo.list(user_id = user.id, done = False, auto_expunge=True)

            # Determine distribution of focus sessions based on some work strategy
            strategy = ChipStrategy()
            time_planner = TimeDistributionPlanner(strategy)
            time_planner.distribute_work_hours(schedules_to_plan, tasks, preference, START_OF_DAY, timezone_format)

            builder.schedule_work_sessions(schedule_date, timezone_format, tasks, preference)
