from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.tasks.repositories import TaskRepository

async def provide_tasks_repo(db_session: AsyncSession) -> TaskRepository:
    """This provides the default Tasks repository"""
    return TaskRepository(session=db_session)