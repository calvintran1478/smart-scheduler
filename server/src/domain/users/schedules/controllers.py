from litestar import Controller, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException, NotFoundException
from litestar.di import Provide

from models.schedule import Schedule
from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from models.habit import RepeatIntervalEnum
from models.user import User
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo
from domain.users.schedules.schemas import CreateFocusSessionInput, UpdateFocusSessionInput, UpdateHabitSessionInput
from domain.users.schedules.dtos import ScheduleDTO, ScheduleItemDTO
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.preferences.dependencies import provide_preferences_repo
from domain.users.events.repositories import EventRepository
from domain.users.events.dependencies import provide_events_repo
from domain.users.events.validators import check_timezone
from domain.users.habits.repositories import HabitRepository
from domain.users.habits.dependencies import provide_habits_repo
from domain.users.tasks.repositories import TaskRepository
from domain.users.tasks.dependencies import provide_tasks_repo
from lib.time import convert_to_utc, seconds_to_time_object, get_time_difference, SECONDS_PER_DAY
from lib.schedule import requires_refresh, requires_week_refresh, ScheduleBuilder

from datetime import date, timedelta
from uuid import UUID

class ScheduleController(Controller):
    dependencies = {
        "schedules_repo": Provide(provide_schedules_repo),
        "preferences_repo": Provide(provide_preferences_repo),
        "events_repo": Provide(provide_events_repo),
        "habits_repo": Provide(provide_habits_repo),
        "tasks_repo": Provide(provide_tasks_repo)
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
        tasks_repo: TaskRepository,
        timezone: str = "UTC"
    ) -> Schedule:
        # Check if the schedule has already been generated
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)

        # If not, or its associated weekly schedule requires a refresh, plan out schedule for the week
        if (schedule == None or (await requires_week_refresh(schedule, timezone, user, habits_repo))):
            weekly_schedule = await schedules_repo.create_weekly_schedule(user, schedule_date, preferences_repo, events_repo, habits_repo, tasks_repo, check_timezone(timezone))
            schedule = weekly_schedule[schedule_date.weekday()]

        # Otherwise return the schedule after refreshing it if necessary
        elif (requires_refresh(schedule, timezone)):
            await schedules_repo.refresh_schedule(user, schedule, preferences_repo, events_repo, habits_repo, check_timezone(timezone))

        return schedule

    @post(path="/{schedule_date:date}/focus-sessions", return_dto=ScheduleItemDTO)
    async def create_focus_session(
        self,
        data: CreateFocusSessionInput,
        user: User,
        schedule_date: date,
        schedules_repo: ScheduleRepository,
        preferences_repo: PreferenceRepository,
        events_repo: EventRepository,
        habits_repo: HabitRepository,
        tasks_repo: TaskRepository,
        timezone: str
    ) -> ScheduleItem:
        # Get schedule
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None or (await requires_week_refresh(schedule, timezone, user, habits_repo))):
            weekly_schedule = await schedules_repo.create_weekly_schedule(user, schedule_date, preferences_repo, events_repo, habits_repo, tasks_repo, check_timezone(timezone))
            schedule = weekly_schedule[schedule_date.weekday()]
        elif (requires_refresh(schedule, timezone)):
            await schedules_repo.refresh_schedule(user, schedule, preferences_repo, events_repo, habits_repo, check_timezone(timezone))

        # Add a new focus session to the schedule
        if (data.start_time == None):
            # Plan focus session for the user based on their preferences
            preference = await preferences_repo.get_one_or_none(user_id = user.id)
            schedule_builder = ScheduleBuilder(schedule)
            focus_session = schedule_builder.add_work_session(data.name, data.duration * 60, preference)
        else:
            # Check if focus session is contained within a single day
            end_time_offset = data.start_time.hour * 3600 + (data.start_time.minute + data.duration) * 60 + data.start_time.second
            if (end_time_offset > SECONDS_PER_DAY):
                raise ClientException(detail="Focus session must be contained within a single day")

            # Create focus session for the user
            focus_session = ScheduleItem(
                name=data.name,
                start_time=data.start_time,
                end_time=seconds_to_time_object(end_time_offset),
                locked=True,
                schedule_item_type=ScheduleItemTypeEnum.FOCUS_SESSION
            )

            # Check if chosen times overlap with existing schedule items
            if any(focus_session.end_time > schedule_item.start_time and focus_session.start_time < schedule_item.end_time for schedule_item in schedule.schedule_items):
                raise ClientException(detail="Chosen times must not overlap with existing schedule items", status_code=HTTP_409_CONFLICT)

            schedule.schedule_items.append(focus_session)

        await schedules_repo.update(schedule, auto_commit=True)

        return focus_session

    @patch(path="/{schedule_date:date}/focus-sessions/{schedule_item_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def update_focus_session(self, data: UpdateFocusSessionInput, user: User, schedule_date: date, schedule_item_id: UUID, schedules_repo: ScheduleRepository) -> None:
        # Get schedule
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None):
            raise NotFoundException(detail="Focus session not found")

        # Search for focus session
        try:
            focus_session = next(schedule_item for schedule_item in schedule.schedule_items if schedule_item.id == schedule_item_id and schedule_item.schedule_item_type == ScheduleItemTypeEnum.FOCUS_SESSION)
        except StopIteration:
            raise NotFoundException(detail="Focus session not found")

        # Update focus session
        for attribute_name, attribute_value in data.__dict__.items():
            if (attribute_value != None):
                setattr(focus_session, attribute_name, attribute_value)
        focus_session.locked = True

        # Check if new time values are valid
        if (focus_session.start_time > focus_session.end_time):
            raise ClientException(detail="Start time must come before end time")

        if any(schedule_item.start_time < focus_session.end_time and schedule_item.end_time > focus_session.start_time and schedule_item.id != focus_session.id for schedule_item in schedule.schedule_items):
            raise ClientException(detail="New times must not overlap with existing schedule items", status_code=HTTP_409_CONFLICT)

        await schedules_repo.update(schedule, auto_commit=True)

    @delete(path="/{schedule_date:date}/focus-sessions/{schedule_item_id:uuid}")
    async def remove_focus_session(self, user: User, schedule_date: date, schedule_item_id: UUID, schedules_repo: ScheduleRepository) -> None:
        # Fetch schedule
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None):
            raise NotFoundException(detail="Focus session not found")

        # Remove focus session from schedule if it exists
        for i, schedule_item in enumerate(schedule.schedule_items):
            if (schedule_item.id == schedule_item_id and schedule_item.schedule_item_type == ScheduleItemTypeEnum.FOCUS_SESSION):
                del schedule.schedule_items[i]
                return

        raise NotFoundException(detail="Focus session not found")

    @patch(path="/{schedule_date:date}/habit-sessions/{schedule_item_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def update_habit_session(self, data: UpdateHabitSessionInput, user: User, schedule_date: date, schedule_item_id: UUID, schedules_repo: ScheduleRepository) -> None:
        # Get schedule
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None):
            raise NotFoundException(detail="Habit session not found")

        # Search for habit session
        try:
            habit_session = next(schedule_item for schedule_item in schedule.schedule_items if schedule_item.id == schedule_item_id and schedule_item.schedule_item_type == ScheduleItemTypeEnum.HABIT)
        except StopIteration:
            raise NotFoundException(detail="Habit session not found")

        # Get habit duration
        duration = get_time_difference(habit_session.start_time, habit_session.end_time)

        # Check if habit session is contained within a single day
        end_time_offset = data.start_time.hour * 3600 + data.start_time.minute * 60 + data.start_time.second + duration
        if (end_time_offset > SECONDS_PER_DAY):
            raise ClientException(detail="Habit session must be contained within a single day")

        # Update habit session
        habit_session.start_time = data.start_time
        habit_session.end_time = seconds_to_time_object(end_time_offset)
        habit_session.locked = True

        # Check if new time values are valid
        if any(schedule_item.start_time < habit_session.end_time and schedule_item.end_time > habit_session.start_time and schedule_item.id != habit_session.id for schedule_item in schedule.schedule_items):
            raise ClientException(detail="New times must not overlap with existing schedule items", status_code=HTTP_409_CONFLICT)

        await schedules_repo.update(schedule, auto_commit=True)

    @delete(path="/{schedule_date:date}/habit-sessions/{schedule_item_id:uuid}")
    async def remove_habit_session(self, user: User, schedule_date: date, schedule_item_id: UUID, schedules_repo: ScheduleRepository, habits_repo: HabitRepository) -> None:
        # Get schedule
        schedule = await schedules_repo.get_one_or_none(user_id=user.id, date=schedule_date)
        if (schedule == None):
            raise NotFoundException(detail="Habit session not found")

        # Search for habit session
        try:
            habit_session = next(schedule_item for schedule_item in schedule.schedule_items if schedule_item.id == schedule_item_id and schedule_item.schedule_item_type == ScheduleItemTypeEnum.HABIT)
        except StopIteration:
            raise NotFoundException(detail="Habit session not found")

        # If weekly habit session was removed reschedule to a new date
        weekly_habits = await habits_repo.list(user_id=user.id, repeat_interval=RepeatIntervalEnum.WEEKLY)
        weekly_habit_names = tuple(habit.name for habit in weekly_habits)
        if (habit_session.name in weekly_habit_names):
            habit = next(habit for habit in weekly_habits if habit.name == habit_session.name)
            candidate_schedules = await schedules_repo.list(Schedule.user_id==user.id, Schedule.date>schedule_date)
            for candidate_schedule in candidate_schedules:
                schedule_builder = ScheduleBuilder(candidate_schedule)
                try:
                    schedule_builder.add_habit_session(habit)
                    schedule.schedule_items.remove(habit_session)
                    return
                except ClientException:
                    pass

        # Remove habit session from schedule
        schedule.schedule_items.remove(habit_session)