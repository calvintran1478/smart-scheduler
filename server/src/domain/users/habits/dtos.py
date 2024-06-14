from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.habit import Habit

class HabitDTO(SQLAlchemyDTO[Habit]):
    config = SQLAlchemyDTOConfig(include={"name", "frequency", "repeat_interval"})