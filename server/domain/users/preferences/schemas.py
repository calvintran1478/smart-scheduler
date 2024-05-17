from pydantic import BaseModel, NonNegativeInt
from datetime import time
from domain.users.preferences.validators import FocusTimes

class SetPreferencesInput(BaseModel):
    wake_up_time: time
    sleep_time: time
    best_focus_times: FocusTimes
    break_length: NonNegativeInt
    tend_to_procrastinate: bool