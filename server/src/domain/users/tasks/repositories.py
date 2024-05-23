from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import delete, and_
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from models.task import Task

class TaskRepository(SQLAlchemyAsyncRepository[Task]):
    """Task repository"""

    model_type = Task

    async def delete_by_user_id_and_task_id(self, user_id: UUID, task_id: UUID) -> None:
        try:
            await self.session.execute(statement=delete(Task).where(and_(Task.user_id == user_id, Task.id == task_id)))
        except IntegrityError:
            await self.session.rollback()
        else:
            await self.session.commit()