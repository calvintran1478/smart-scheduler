from litestar import Controller, Response, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.exceptions import NotFoundException
from litestar.dto import DTOData
from litestar.di import Provide

from models.task import Task
from models.user import User
from domain.users.tasks.repositories import TaskRepository
from domain.users.tasks.dependencies import provide_tasks_repo, provide_task
from domain.users.tasks.schemas import CreateTaskInput, UpdateTaskInput
from domain.users.tasks.dtos import TaskDTO, UpdateTaskDTO
from domain.users.tasks.hooks import after_task_get_request
from domain.users.tags.repositories import TagRepository
from domain.users.tags.dependencies import provide_tags_repo

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
    async def get_task(self, task: Task) -> Task:
        return task

    @patch(path="/{task_id:str}", dto=UpdateTaskDTO)
    async def update_task(self, data: DTOData[UpdateTaskInput], user: User, task: Task, tags_repo: TagRepository) -> None:
        # Perform normal update if tag was not changed
        tag_name = data.create_instance().tag
        if (tag_name == None):
            data.update_instance(task)

        # If tag was changed, first check the new tag exists before updating
        else:
            tag = await tags_repo.get_one_or_none(user_id=user.id, name=tag_name)
            if (tag == None):
                raise NotFoundException(detail="Tag not found")
            data.update_instance(task, tag=tag)

        return Response(content="", status_code=HTTP_204_NO_CONTENT)

    @delete(path="/{task_id:str}")
    async def remove_task(self, task: Task, tasks_repo: TaskRepository) -> None:
        await tasks_repo.delete(task.id)

    @delete(path="/{task_id:str}/tag")
    async def remove_task_tag(self, task: Task, tasks_repo: TaskRepository) -> None:
        # Remove tag from task
        task.tag = None
        await tasks_repo.update(task, auto_commit=True)