from litestar import Controller, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT
from litestar.exceptions import NotFoundException
from litestar.response import ServerSentEvent
from litestar.channels import ChannelsPlugin
from litestar.di import Provide

from models.task import Task
from models.user import User
from models.schedule_item import ScheduleItemTypeEnum
from domain.users.tasks.repositories import TaskRepository
from domain.users.tasks.dependencies import provide_tasks_repo, provide_task
from domain.users.tasks.schemas import CreateTaskInput, UpdateTaskInput
from domain.users.tasks.dtos import TaskDTO
from domain.users.tasks.hooks import after_task_get_request
from domain.users.tasks.validators import check_timezone
from domain.users.tags.repositories import TagRepository
from domain.users.tags.dependencies import provide_tags_repo
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo
from lib.time import convert_to_utc
from lib.sse import sse_generator

from datetime import datetime
from uuid import UUID
from typing import Optional
from asyncio import gather

class TaskController(Controller):
    dependencies = {
        "tasks_repo": Provide(provide_tasks_repo),
        "tags_repo": Provide(provide_tags_repo),
        "schedules_repo": Provide(provide_schedules_repo),
        "task": Provide(provide_task)
    }

    @get(path="/sse", sync_to_thread=False)
    def sse_handler(self, channels: ChannelsPlugin, user: User, client_id: UUID) -> ServerSentEvent:
        return ServerSentEvent(sse_generator(channels, user, client_id, "tasks"))

    @post(path="/", return_dto=TaskDTO)
    async def create_task(self, data: CreateTaskInput, channels: ChannelsPlugin, user: User, client_id: UUID, tasks_repo: TaskRepository, tags_repo: TagRepository, schedules_repo: ScheduleRepository) -> Task:
        # Check tag exists if one was included
        tag = None
        if (data.tag != None):
            tag = await tags_repo.get_one_or_none(user_id=user.id, name=data.tag, auto_expunge=True)
            if (tag == None):
                raise NotFoundException(detail="Tag not found")

        # Create task for the user
        task = Task(
            name = data.name,
            deadline = convert_to_utc(data.timezone, datetime.combine(data.deadline_date, data.deadline_time)),
            time_estimate = data.time_estimate,
            tag = tag,
            user_id = user.id
        )

        await gather(
            tasks_repo.add(task, auto_expunge=True),
            schedules_repo.mark_schedules_for_refresh(user.id, (ScheduleItemTypeEnum.FOCUS_SESSION,))
        )

        task.deadline = task.deadline.astimezone(data.timezone)

        # Send server event
        channels.publish({
            "event": "task added",
            "origin_client": client_id,
            "task": {
                "task_id": task.id,
                "name": task.name,
                "deadline_date": task.deadline,
                "time_estimate": task.time_estimate,
                "minutes_completed": task.minutes_completed,
                "done": task.done,
                "tag": (None if data.tag == None else {"name": tag.name, "colour": tag.colour})
            }
        }, f"tasks_{user.id}")

        return task

    @get(path="/", return_dto=TaskDTO, after_request=after_task_get_request)
    async def get_tasks(self, user: User, tasks_repo: TaskRepository, timezone: Optional[str] = None) -> list[Task]:
        # Get user tasks
        tasks = await tasks_repo.list(user_id = user.id, auto_expunge=True)

        # Convert deadlines to the specified timezone if one was given
        if (timezone != None):
            timezone_format = check_timezone(timezone)
            for task in tasks:
                task.deadline = task.deadline.astimezone(timezone_format)

        return tasks

    @patch(path="/{task_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def update_task(self, data: UpdateTaskInput, channels: ChannelsPlugin, user: User, client_id: UUID, task: Task, tasks_repo: TaskRepository, tags_repo: TagRepository, schedules_repo: ScheduleRepository) -> None:      
        # Handle tag update
        if (data.tag != None):
            task.tag = await tags_repo.get_one_or_none(user_id=user.id, name=data.tag, auto_expunge=True)
            if (task.tag == None):
                raise NotFoundException(detail="Tag not found")

        # Update remaining attributes
        for attribute_name, attribute_value in data.__dict__.items():
            if attribute_value != None and attribute_name not in ["tag", "timezone"]:
                setattr(task, attribute_name, attribute_value)

        await gather(
            tasks_repo.update(task, auto_expunge=True),
            schedules_repo.mark_schedules_for_refresh(user.id, (ScheduleItemTypeEnum.FOCUS_SESSION,))
        )

        # Send server event
        channels.publish({
            "event": "task updated",
            "origin_client": client_id,
            "task": {
                "task_id": task.id,
                "name": task.name,
                "deadline_date": task.deadline,
                "time_estimate": task.time_estimate,
                "minutes_completed": task.minutes_completed,
                "done": task.done,
                "tag": (None if data.tag == None else {"name": task.tag.name, "colour": task.tag.colour})
            }
        }, f"tasks_{user.id}")

    @delete(path="/{task_id:str}")
    async def remove_task(self, channels: ChannelsPlugin, user: User, client_id: UUID, task: Task, tasks_repo: TaskRepository, schedules_repo: ScheduleRepository) -> None:
        await gather(
            tasks_repo.delete(task.id, auto_expunge=True),
            schedules_repo.mark_schedules_for_refresh(user.id, (ScheduleItemTypeEnum.FOCUS_SESSION,))
        )

        # Send server event
        channels.publish({"event": "task deleted", "origin_client": client_id, "task_id": task.id}, f"tasks_{user.id}")

    @delete(path="/{task_id:str}/tag")
    async def remove_task_tag(self, channels: ChannelsPlugin, user: User, client_id: UUID, task: Task, tasks_repo: TaskRepository) -> None:
        # Remove tag from task
        if (task.tag == None):
            raise NotFoundException(detail="Tag not found")
        task.tag = None

        await tasks_repo.update(task, auto_expunge=True)

        # Send server event
        channels.publish({"event": "task tag removed", "origin_client": client_id, "task_id": task.id}, f"tasks_{user.id}")
