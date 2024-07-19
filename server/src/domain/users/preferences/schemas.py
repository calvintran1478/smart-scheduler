from pydantic import BaseModel, NonNegativeInt, model_validator
from datetime import time
from typing_extensions import Self
from litestar.exceptions import ClientException
from domain.users.preferences.validators import FocusTimes
from lib.time import get_time_difference

class SetPreferencesInput(BaseModel):
    wake_up_time: time
    sleep_time: time
    start_of_work_day: time
    end_of_work_day: time
    best_focus_times: FocusTimes
    break_length: NonNegativeInt

    @model_validator(mode="after")
    def validate_preferences(self) -> Self:
        # Compare time choices relative to wake up time
        t1 = get_time_difference(self.wake_up_time, self.start_of_work_day)
        t2 = get_time_difference(self.wake_up_time, self.end_of_work_day)
        t3 = get_time_difference(self.wake_up_time, self.sleep_time)

        # Check that the chosen work hours are a subset of awake hours
        valid_time_choice = (0 <= t1 <= t2 <= t3)
        if (not valid_time_choice):
            raise ClientException(detail="Work hours cannot overlap with sleep hours")

        return self