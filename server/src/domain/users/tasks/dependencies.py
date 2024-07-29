from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException
from uuid import UUID
from models.user import User
from models.task import Task
from domain.users.tasks.repositories import TaskRepository

async def provide_tasks_repo(db_session: AsyncSession) -> TaskRepository:
    """This provides the default Tasks repository"""
    return TaskRepository(session=db_session)

async def provide_task(user: User, task_id: str, tasks_repo: TaskRepository) -> Task:
    """This provides the task belonging to the user identified by the task id"""
    # Check for valid uuid
    try:
        UUID(task_id)
    except ValueError:
        raise NotFoundException(detail="Task not found")

    # Get task by user id and task id
    task = await tasks_repo.get_one_or_none(user_id=user.id, id=task_id)
    if (task == None):
        raise NotFoundException(detail="Task not found")

    return task