from litestar import Controller, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException
from litestar.response import ServerSentEvent
from litestar.channels import ChannelsPlugin
from litestar.di import Provide

from models.user import User
from models.habit import Habit, TimePrefererenceEnum
from models.habit_completion import HabitCompletion
from models.schedule_item import ScheduleItemTypeEnum
from domain.users.habits.repositories import HabitRepository, HabitCompletionRepository
from domain.users.habits.dependencies import provide_habits_repo, provide_habit_completions_repo, provide_habit
from domain.users.habits.schemas import CreateHabitInput, UpdateHabitInput, CompleteHabitInput
from domain.users.habits.dtos import HabitDTO, HabitCompletionDTO
from domain.users.habits.hooks import after_habit_get_request
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo
from lib.sse import sse_generator

class HabitController(Controller):
    dependencies = {
        "habits_repo": Provide(provide_habits_repo),
        "habit_completions_repo": Provide(provide_habit_completions_repo),
        "schedules_repo": Provide(provide_schedules_repo),
        "habit": Provide(provide_habit)
    }

    @get(path="/sse", sync_to_thread=False)
    def sse_handler(self, channels: ChannelsPlugin, user: User) -> ServerSentEvent:
        return ServerSentEvent(sse_generator(channels, user, "habits"))

    @post(path="/", return_dto=HabitDTO)
    async def create_habit(self, data: CreateHabitInput, channels: ChannelsPlugin, user: User, habits_repo: HabitRepository, schedules_repo: ScheduleRepository) -> Habit:
        # Check if habit with name already exists
        habit_exists = await habits_repo.exists(user_id=user.id, name=data.name)
        if habit_exists:
            raise ClientException(detail="Habit with the given name already exists", status_code=HTTP_409_CONFLICT)

        # Create habit for the user
        habit = Habit(
            user_id=user.id,
            name=data.name,
            frequency=data.frequency,
            duration=data.duration,
            repeat_interval=data.repeat_interval,
            morning_preferred=TimePrefererenceEnum.MORNING in data.time_preference,
            afternoon_preferred=TimePrefererenceEnum.AFTERNOON in data.time_preference,
            evening_preferred=TimePrefererenceEnum.EVENING in data.time_preference,
            night_preferred=TimePrefererenceEnum.NIGHT in data.time_preference
        )

        await habits_repo.add(habit, auto_expunge=True)

        # Mark schedules for refresh
        await schedules_repo.mark_schedules_for_refresh(user.id, (ScheduleItemTypeEnum.HABIT, ScheduleItemTypeEnum.FOCUS_SESSION))

        # Send server event
        channels.publish({
            "event": "habit added",
            "habit": {
                "name": habit.name,
                "frequency": habit.frequency,
                "duration": habit.duration,
                "repeat_interval": habit.repeat_interval,
                "morning_preferred": habit.morning_preferred,
                "afternoon_preferred": habit.afternoon_preferred,
                "evening_preferred": habit.evening_preferred,
                "night_preferred": habit.night_preferred
            }
        }, f"habits_{user.id}")

        return habit

    @get(path="/", return_dto=HabitDTO, after_request=after_habit_get_request)
    async def get_habits(self, user: User, habits_repo: HabitRepository) -> list[Habit]:
        return await habits_repo.list(user_id = user.id, auto_expunge=True)

    @patch(path="/{habit_name:str}", status_code=HTTP_204_NO_CONTENT)
    async def update_habit(self, data: UpdateHabitInput, channels: ChannelsPlugin, user: User, habit: Habit, habits_repo: HabitRepository, schedules_repo: ScheduleRepository) -> None:
        # Check if any habits have the same name as the updated value
        if (data.name != None and data.name != habit.name):
            habit_exists = await habits_repo.exists(user_id=user.id, name=data.name)
            if habit_exists:
                raise ClientException(detail="Habit with the given name already exists", status_code=HTTP_409_CONFLICT)

        # Update time preferences
        if (data.time_preference != None):
            habit.morning_preferred = TimePrefererenceEnum.MORNING in data.time_preference
            habit.afternoon_preferred = TimePrefererenceEnum.AFTERNOON in data.time_preference
            habit.evening_preferred = TimePrefererenceEnum.EVENING in data.time_preference
            habit.night_preferred = TimePrefererenceEnum.NIGHT in data.time_preference

        # Update habit
        for attribute_name, attribute_value in data.__dict__.items():
            if attribute_value != None and attribute_name != "time_preference":
                setattr(habit, attribute_name, attribute_value)

        await habits_repo.update(habit, auto_commit=True)

        # Mark schedules for refresh
        await schedules_repo.mark_schedules_for_refresh(user.id, (ScheduleItemTypeEnum.HABIT, ScheduleItemTypeEnum.FOCUS_SESSION))

        # Send server event
        channels.publish({
            "event": "habit updated",
            "habit": {
                "name": habit.name,
                "frequency": habit.frequency,
                "duration": habit.duration,
                "repeat_interval": habit.repeat_interval,
                "morning_preferred": habit.morning_preferred,
                "afternoon_preferred": habit.afternoon_preferred,
                "evening_preferred": habit.evening_preferred,
                "night_preferred": habit.night_preferred
            }
        }, f"habits_{user.id}")

    @delete(path="/{habit_name:str}")
    async def remove_habit(self, channels: ChannelsPlugin, user: User, habit: Habit, habits_repo: HabitRepository, schedules_repo: ScheduleRepository) -> None:
        await habits_repo.delete(habit.id, auto_expunge=True)

        # Mark schedules for refresh
        await schedules_repo.mark_schedules_for_refresh(user.id, (ScheduleItemTypeEnum.HABIT, ScheduleItemTypeEnum.FOCUS_SESSION))

        # Send server event
        channels.publish({"event": "habit deleted", "habit_name": habit.name}, f"habits_{user.id}")

    @post(path="/{habit_name:str}/completions", return_dto=HabitCompletionDTO)
    async def complete_habit(self, data: CompleteHabitInput, habit: Habit, habit_completions_repo: HabitCompletionRepository) -> HabitCompletion:
        # Check if habit was completed earlier this date
        habit_completion = await habit_completions_repo.get_one_or_none(user_id=habit.user_id, habit_name=habit.name, completion_date=data.completion_date)

        # Increment completion count
        if (habit_completion != None):
            habit_completion.count += 1
            await habit_completions_repo.update(habit_completion, auto_commit=True)
        else:
            habit_completion = HabitCompletion(user_id=habit.user_id, habit_name=habit.name, completion_date=data.completion_date)
            await habit_completions_repo.add(habit_completion, auto_commit=True)

        return habit_completion
