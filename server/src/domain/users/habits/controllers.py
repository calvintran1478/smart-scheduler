from litestar import Controller, Response, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException
from litestar.di import Provide

from models.user import User
from models.habit import Habit
from domain.users.habits.repositories import HabitRepository
from domain.users.habits.dependencies import provide_habits_repo, provide_habit
from domain.users.habits.schemas import CreateHabitInput, UpdateHabitInput
from domain.users.habits.dtos import HabitDTO
from domain.users.habits.hooks import after_habit_get_request

class HabitController(Controller):
    dependencies = {"habits_repo": Provide(provide_habits_repo), "habit": Provide(provide_habit)}

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
            repeat_interval=data.repeat_interval
        )

        await habits_repo.add(habit, auto_commit=True)

        return habit

    @get(path="/", return_dto=HabitDTO, after_request=after_habit_get_request)
    async def get_habits(self, user: User, habits_repo: HabitRepository) -> list[Habit]:
        return await habits_repo.list(user_id = user.id)

    @patch(path="/{habit_name:str}")
    async def update_habit(self, data: UpdateHabitInput, user: User, habit: Habit, habits_repo: HabitRepository) -> None:
        # Check if any habits have the same name as the updated value
        if (data.name != None and data.name != habit.name):
            habit_exists = await habits_repo.exists(user_id=user.id, name=data.name)
            if habit_exists:
                raise ClientException(detail="Habit with the given name already exists", status_code=HTTP_409_CONFLICT)

        # Update habit
        for attribute_name, attribute_value in data.__dict__.items():
            if attribute_value != None:
                setattr(habit, attribute_name, attribute_value)

        await habits_repo.update(habit, auto_commit=True)

        return Response(content="", status_code=HTTP_204_NO_CONTENT)

    @delete(path="/{habit_name:str}")
    async def remove_habit(self, habit: Habit, habits_repo: HabitRepository) -> None:
        await habits_repo.delete(habit.id)