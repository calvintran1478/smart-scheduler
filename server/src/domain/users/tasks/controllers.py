from litestar import Controller, Response, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.exceptions import NotFoundException
from litestar.di import Provide

from models.task import Task
from models.user import User
from domain.users.tasks.repositories import TaskRepository
from domain.users.tasks.dependencies import provide_tasks_repo
from domain.users.tasks.schemas import CreateTaskInput, UpdateTaskInput
from domain.users.tasks.dtos import TaskDTO
from domain.users.tasks.hooks import after_task_get_request
from domain.users.tags.repositories import TagRepository
from domain.users.tags.dependencies import provide_tags_repo

from uuid import UUID

class TaskController(Controller):
    dependencies = {"tasks_repo": Provide(provide_tasks_repo), "tags_repo": Provide(provide_tags_repo)}

    @post(path="/", return_dto=TaskDTO)
    async def create_task(self, data: CreateTaskInput, user: User, tasks_repo: TaskRepository, tags_repo: TagRepository) -> Task:
        # Check tag exists if one was included
        tag_id = None
        if (data.tag != None):
            tag = await tags_repo.get_one_or_none(user_id=user.id, name=data.tag)
            if (tag == None):
                raise NotFoundException(detail="Tag not found")
            tag_id = tag.id

        # Create task for the user
        task = Task(
            name = data.name,
            deadline_date = data.deadline_date,
            deadline_time = data.deadline_time,
            tag_id = tag_id,
            user_id = user.id
        )

        await tasks_repo.add(task, auto_commit=True)

        return task

    @get(path="/", return_dto=TaskDTO, after_request=after_task_get_request)
    async def get_tasks(self, user: User, tasks_repo: TaskRepository) -> list[Task]:
        return await tasks_repo.list(user_id = user.id)

    @get(path="/{task_id:str}", return_dto=TaskDTO)
    async def get_task(self, user: User, task_id: str, tasks_repo: TaskRepository) -> Task:
        # Check for valid uuid
        try:
            UUID(task_id)
        except ValueError:
            raise NotFoundException(detail="Task not found")

        # Check if task exists
        task = await tasks_repo.get_one_or_none(user_id=user.id, id=task_id)
        if (task == None):
            raise NotFoundException(detail="Task not found")
        return task

    @patch(path="/{task_id:str}")
    async def update_task(self, data: UpdateTaskInput, user: User, task_id:str, tasks_repo: TaskRepository, tags_repo: TagRepository) -> None:
        # Check for valid uuid
        try:
            UUID(task_id)
        except ValueError:
            raise NotFoundException(detail="Task not found")

        # Check if task exists
        task = await tasks_repo.get_one_or_none(user_id=user.id, id=task_id)
        if (task == None):
            raise NotFoundException(detail="Task not found")

        # Check tag exists if one was included
        tag = None
        if (data.tag != None):
            tag = await tags_repo.get_one_or_none(user_id=user.id, name=data.tag)
            if (tag == None):
                raise NotFoundException(detail="Tag not found")

        # Update task values
        task.name = data.name if data.name != None else task.name
        task.deadline_date = data.deadline_date if data.deadline_date != None else task.deadline_date
        task.deadline_time = data.deadline_time if data.deadline_time != None else task.deadline_time
        task.done = data.done if data.done != None else task.done
        task.tag = tag if data.tag != None else task.tag

        await tasks_repo.update(task, auto_commit=True)

        return Response(content="", status_code=HTTP_204_NO_CONTENT)

    @delete(path="/{task_id:str}")
    async def remove_task(self, user: User, task_id: str, tasks_repo: TaskRepository) -> None:
        await tasks_repo.delete_by_user_id_and_task_id(user.id, task_id)

    @delete(path="/{task_id:str}/tag")
    async def remove_task_tag(self, user: User, task_id: str, tasks_repo: TaskRepository) -> None:
        # Check for valid uuid
        try:
            UUID(task_id)
        except ValueError:
            raise NotFoundException(detail="Task not found")

        # Check if task exists
        task = await tasks_repo.get_one_or_none(user_id=user.id, id=task_id)
        if (task == None):
            raise NotFoundException(detail="Task not found")

        # Remove tag from task
        task.tag = None
        await tasks_repo.update(task, auto_commit=True)