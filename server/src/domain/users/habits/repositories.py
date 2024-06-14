from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.habit import Habit

class HabitRepository(SQLAlchemyAsyncRepository[Habit]):
    """Habit repository"""

    model_type = Habit