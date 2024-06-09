from pydantic import BaseModel, NaiveDatetime, model_validator
from typing import Optional
from typing_extensions import Self
from litestar.exceptions import ClientException
from domain.users.events.validators import RepeatRule, TimeZone

import datetime

class CreateEventInput(BaseModel):
    summary: str
    start_time: NaiveDatetime
    end_time: NaiveDatetime
    timezone: TimeZone
    description: Optional[str] = None
    location: Optional[str] = None
    repeat_rule: Optional[RepeatRule] = "NEVER"

    @model_validator(mode="after")
    def validate_event(self) -> Self:
        if self.start_time > self.end_time:
            raise ClientException(detail="Start time must come before end time")

        return self

class UpdateEventInput(BaseModel):
    summary: Optional[str] = None
    start_time: Optional["datetime.datetime"] = None
    end_time: Optional["datetime.datetime"] = None
    timezone: Optional[TimeZone] = None
    description: Optional[str] = None
    location: Optional[str] = None
    repeat_rule: Optional[RepeatRule] = None