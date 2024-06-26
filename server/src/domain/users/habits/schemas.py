from pydantic import BaseModel, PositiveInt
from typing import Optional
from domain.users.habits.validators import HabitName, RepeatInterval

class CreateHabitInput(BaseModel):
    name: HabitName
    frequency: PositiveInt
    duration: PositiveInt
    repeat_interval: RepeatInterval

class UpdateHabitInput(BaseModel):
    name: Optional[HabitName] = None
    frequency: Optional[PositiveInt] = None
    duration: Optional[PositiveInt] = None
    repeat_interval: Optional[RepeatInterval] = None