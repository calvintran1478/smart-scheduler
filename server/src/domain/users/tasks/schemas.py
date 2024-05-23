from pydantic import BaseModel
from typing import Optional
from datetime import date, time
import datetime

class CreateTaskInput(BaseModel):
    name: str
    deadline_date: date
    deadline_time: Optional["datetime.time"] = time(23, 59, 59)
    tag: Optional[str] = None

class UpdateTaskInput(BaseModel):
    name: Optional[str] = None
    deadline_date: Optional["datetime.date"] = None
    deadline_time: Optional["datetime.time"] = None
    done: Optional[bool] = None
    tag: Optional[str] = None