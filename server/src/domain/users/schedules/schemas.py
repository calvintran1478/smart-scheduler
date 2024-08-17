from pydantic import BaseModel, model_validator
from typing import Optional
from typing_extensions import Self
from litestar.exceptions import ClientException
from datetime import time
from domain.users.schedules.validators import MinuteDuration

import datetime

class CreateFocusSessionInput(BaseModel):
    name: str
    duration: MinuteDuration
    start_time: Optional["datetime.time"] = None

class UpdateFocusSessionInput(BaseModel):
    name: Optional[str] = None
    start_time: Optional["datetime.time"] = None
    end_time: Optional["datetime.time"] = None

class UpdateHabitSessionInput(BaseModel):
    start_time: time
