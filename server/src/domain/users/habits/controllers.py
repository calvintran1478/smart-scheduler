from litestar import Controller, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException
from litestar.di import Provide

from models.user import User
from models.habit import Habit, TimePrefererenceEnum
from models.habit_completion import HabitCompletion
from domain.users.habits.repositories import HabitRepository, HabitCompletionRepository
from domain.users.habits.dependencies import provide_habits_repo, provide_habit_completions_repo, provide_habit
from domain.users.habits.schemas import CreateHabitInput, UpdateHabitInput, CompleteHabitInput
from domain.users.habits.dtos import HabitDTO, HabitCompletionDTO
from domain.users.habits.hooks import after_habit_get_request

class HabitController(Controller):
    dependencies = {"habits_repo": Provide(provide_habits_repo), "habit_completions_repo": Provide(provide_habit_completions_repo), "habit": Provide(provide_habit)}

    @post(path="/", return_dto=HabitDTO)
    async def create_habit(self, data: CreateHabitInput, user: User, habits_repo: HabitRepository) -> Habit:
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

        await habits_repo.add(habit, auto_commit=True)

        return habit

    @get(path="/", return_dto=HabitDTO, after_request=after_habit_get_request)
    async def get_habits(self, user: User, habits_repo: HabitRepository) -> list[Habit]:
        return await habits_repo.list(user_id = user.id)

    @patch(path="/{habit_name:str}", status_code=HTTP_204_NO_CONTENT)
    async def update_habit(self, data: UpdateHabitInput, user: User, habit: Habit, habits_repo: HabitRepository) -> None:
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

    @delete(path="/{habit_name:str}")
    async def remove_habit(self, habit: Habit, habits_repo: HabitRepository) -> None:
        await habits_repo.delete(habit.id, auto_commit=True)

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