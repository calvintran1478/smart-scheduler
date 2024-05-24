from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from models.task import Task
from domain.users.tasks.schemas import UpdateTaskInput

class TaskDTO(SQLAlchemyDTO[Task]):
    config = SQLAlchemyDTOConfig(
        include={"id", "name", "deadline_date", "deadline_time", "done", "tag.0.name", "tag.0.colour"},
        rename_fields={"id": "task_id"},
    )

class UpdateTaskDTO(PydanticDTO[UpdateTaskInput]):
    config = DTOConfig(partial=True)