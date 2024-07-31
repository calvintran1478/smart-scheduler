from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException
from domain.users.habits.repositories import HabitRepository, HabitCompletionRepository
from models.user import User
from models.habit import Habit

async def provide_habits_repo(db_session: AsyncSession) -> HabitRepository:
    """This provides the default Habits repository"""
    return HabitRepository(session=db_session)

async def provide_habit_completions_repo(db_session: AsyncSession) -> HabitCompletionRepository:
    """This provides the default HabitCompletions repository"""
    return HabitCompletionRepository(session=db_session)

async def provide_habit(user: User, habit_name: str, habits_repo: HabitRepository) -> Habit:
    """This provides the habit belonging to the user identified by the habit name"""
    habit = await habits_repo.get_one_or_none(user_id=user.id, name=habit_name)
    if (habit == None):
        raise NotFoundException(detail="Habit not found")

    return habit