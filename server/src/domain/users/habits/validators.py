from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from litestar.exceptions import ClientException
from models.habit import RepeatIntervalEnum, TimePrefererenceEnum

def check_habit_name(habit_name: str) -> str:
    if (habit_name == ""):
        raise ClientException("Habit name cannot be empty")

    return habit_name

def check_habit_repeat_interval(repeat_interval: str) -> str:
    normalized_repeat_interval = repeat_interval.upper()
    if not normalized_repeat_interval in RepeatIntervalEnum:
        raise ClientException("Invalid repeat interval")

    return normalized_repeat_interval

def check_habit_time_preference(time_preference: list[str]) -> list[str]:
    # Count the number of times each preference choice is included
    morning_count = time_preference.count(TimePrefererenceEnum.MORNING)
    afternoon_count = time_preference.count(TimePrefererenceEnum.AFTERNOON)
    evening_count = time_preference.count(TimePrefererenceEnum.EVENING)
    night_count = time_preference.count(TimePrefererenceEnum.NIGHT)

    # Check that each preference choice is included at most once
    time_preference_counts = [morning_count, afternoon_count, evening_count, night_count]
    if any(count > 1 for count in time_preference_counts):
        raise ClientException("Time preference choices should only be included once")

    # Check that no invalid choices are included
    if sum(time_preference_counts) != len(time_preference):
        raise ClientException(f"Time preference choices are only '{TimePrefererenceEnum.MORNING.value}', '{TimePrefererenceEnum.AFTERNOON.value}', '{TimePrefererenceEnum.EVENING.value}', and '{TimePrefererenceEnum.NIGHT.value}'")

    return time_preference

HabitName = Annotated[str, AfterValidator(check_habit_name)]
RepeatInterval = Annotated[str, AfterValidator(check_habit_repeat_interval)]
HabitTimePreference = Annotated[list[str], AfterValidator(check_habit_time_preference)]