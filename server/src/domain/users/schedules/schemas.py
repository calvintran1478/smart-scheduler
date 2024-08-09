from pydantic import BaseModel, model_validator
from typing import Optional
from typing_extensions import Self
from litestar.exceptions import ClientException
from datetime import time

import datetime

class CreateFocusSessionInput(BaseModel):
    name: str
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_focus_session(self) -> Self:
        if (self.start_time > self.end_time):
            raise ClientException(detail="Start time must come before end time")

        return self

class UpdateFocusSessionInput(BaseModel):
    name: Optional[str] = None
    start_time: Optional["datetime.time"] = None
    end_time: Optional["datetime.time"] = None

class UpdateHabitSessionInput(BaseModel):
    start_time: time