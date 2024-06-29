from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.habit import Habit
from models.habit_completion import HabitCompletion

class HabitDTO(SQLAlchemyDTO[Habit]):
    config = SQLAlchemyDTOConfig(include={"name", "frequency", "duration", "repeat_interval"})

class HabitCompletionDTO(SQLAlchemyDTO[HabitCompletion]):
    config = SQLAlchemyDTOConfig(include={"completion_date", "count"})