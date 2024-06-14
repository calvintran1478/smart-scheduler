from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from litestar.exceptions import ClientException
from models.habit import RepeatIntervalEnum

def check_habit_name(habit_name: str) -> str:
    if (habit_name == ""):
        raise ClientException("Habit name cannot be empty")

    return habit_name.replace(" ", "-")

def check_habit_repeat_interval(repeat_interval: str) -> str:
    normalized_repeat_interval = repeat_interval.upper()
    if not normalized_repeat_interval in RepeatIntervalEnum:
        raise ClientException("Invalid repeat interval")

    return normalized_repeat_interval

HabitName = Annotated[str, AfterValidator(check_habit_name)]
RepeatInterval = Annotated[str, AfterValidator(check_habit_repeat_interval)]