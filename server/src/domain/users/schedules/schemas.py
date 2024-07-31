from pydantic import BaseModel
from typing import Optional

import datetime

class UpdateScheduleItemInput(BaseModel):
    start_time: Optional["datetime.time"] = None
    end_time: Optional["datetime.time"] = None