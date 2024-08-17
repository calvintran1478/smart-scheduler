from pydantic import BaseModel, PositiveInt
from typing import Optional
from datetime import date
from domain.users.habits.validators import HabitName, MinuteDuration, RepeatInterval, HabitTimePreference

class CreateHabitInput(BaseModel):
    name: HabitName
    frequency: PositiveInt
    duration: MinuteDuration
    repeat_interval: RepeatInterval
    time_preference: HabitTimePreference

class UpdateHabitInput(BaseModel):
    name: Optional[HabitName] = None
    frequency: Optional[PositiveInt] = None
    duration: Optional[MinuteDuration] = None
    repeat_interval: Optional[RepeatInterval] = None
    time_preference: Optional[HabitTimePreference] = None

class CompleteHabitInput(BaseModel):
    completion_date: date
