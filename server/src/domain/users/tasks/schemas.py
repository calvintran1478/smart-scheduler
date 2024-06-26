from pydantic import BaseModel, model_validator
from typing import Optional
from typing_extensions import Self
from datetime import date, time
from litestar.exceptions import ClientException
from domain.users.tasks.validators import TimeZone
from lib.time import convert_to_utc
import datetime

class CreateTaskInput(BaseModel):
    name: str
    deadline_date: date
    deadline_time: Optional["datetime.time"] = time(23, 59, 59)
    timezone: TimeZone
    tag: Optional[str] = None

class UpdateTaskInput(BaseModel):
    name: Optional[str] = None
    deadline: Optional["datetime.datetime"] = None
    timezone: Optional[TimeZone] = None
    done: Optional[bool] = None
    tag: Optional[str] = None

    @model_validator(mode="after")
    def validate_task_update(self) -> Self:
        # Integrate timezone information into deadline if performing deadline change
        if (self.deadline != None):
            if (self.timezone == None):
                raise ClientException(detail="Missing required timezone info for time change")
            self.deadline = convert_to_utc(self.timezone, self.deadline)

        return self