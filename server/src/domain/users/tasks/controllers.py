from litestar import Controller, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.exceptions import NotFoundException
from litestar.di import Provide

from models.task import Task
from models.user import User
from domain.users.tasks.repositories import TaskRepository
from domain.users.tasks.dependencies import provide_tasks_repo, provide_task
from domain.users.tasks.schemas import CreateTaskInput, UpdateTaskInput
from domain.users.tasks.dtos import TaskDTO
from domain.users.tasks.hooks import after_task_get_request
from domain.users.tasks.validators import check_timezone
from domain.users.tags.repositories import TagRepository
from domain.users.tags.dependencies import provide_tags_repo
from lib.time import convert_to_utc

from datetime import datetime
from typing import Optional

class TaskController(Controller):
    dependencies = {"tasks_repo": Provide(provide_tasks_repo), "tags_repo": Provide(provide_tags_repo), "task": Provide(provide_task)}

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
            deadline = convert_to_utc(data.timezone, datetime.combine(data.deadline_date, data.deadline_time)),
            time_estimate = data.time_estimate,
            tag_id = tag_id,
            user_id = user.id
        )

        await tasks_repo.add(task, auto_commit=True)
        task.deadline = task.deadline.astimezone(data.timezone)

        return task

    @get(path="/", return_dto=TaskDTO, after_request=after_task_get_request)
    async def get_tasks(self, user: User, tasks_repo: TaskRepository, timezone: Optional[str] = None) -> list[Task]:
        # Get user tasks
        tasks = await tasks_repo.list(user_id = user.id)

        # Convert deadlines to the specified timezone if one was given
        if (timezone != None):
            timezone_format = check_timezone(timezone)
            for task in tasks:
                task.deadline = task.deadline.astimezone(timezone_format)

        return tasks

    @patch(path="/{task_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def update_task(self, data: UpdateTaskInput, user: User, task: Task, tasks_repo: TaskRepository, tags_repo: TagRepository) -> None:      
        # Handle tag update
        if (data.tag != None):
            task.tag = await tags_repo.get_one_or_none(user_id=user.id, name=data.tag)
            if (task.tag == None):
                raise NotFoundException(detail="Tag not found")

        # Update remaining attributes
        for attribute_name, attribute_value in data.__dict__.items():
            if attribute_value != None and attribute_name not in ["tag", "timezone"]:
                setattr(task, attribute_name, attribute_value)

        await tasks_repo.update(task, auto_commit=True)

    @delete(path="/{task_id:str}")
    async def remove_task(self, task: Task, tasks_repo: TaskRepository) -> None:
        await tasks_repo.delete(task.id, auto_commit=True)

    @delete(path="/{task_id:str}/tag")
    async def remove_task_tag(self, task: Task, tasks_repo: TaskRepository) -> None:
        # Remove tag from task
        if (task.tag == None):
            raise NotFoundException(detail="Tag not found")
        task.tag = None

        await tasks_repo.update(task, auto_commit=True)