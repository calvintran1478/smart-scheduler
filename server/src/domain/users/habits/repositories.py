from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.habit import Habit
from models.habit_completion import HabitCompletion

class HabitRepository(SQLAlchemyAsyncRepository[Habit]):
    """Habit repository"""

    model_type = Habit


class HabitCompletionRepository(SQLAlchemyAsyncRepository[HabitCompletion]):
    """Habit Completion repository"""

    model_type = HabitCompletion