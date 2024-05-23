from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.task import Task

class TaskRepository(SQLAlchemyAsyncRepository[Task]):
    """Task repository"""

    model_type = Task