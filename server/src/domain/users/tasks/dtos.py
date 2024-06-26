from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.task import Task

class TaskDTO(SQLAlchemyDTO[Task]):
    config = SQLAlchemyDTOConfig(
        include={"id", "name", "deadline", "done", "tag.0.name", "tag.0.colour"},
        rename_fields={"id": "task_id"},
    )