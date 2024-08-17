from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from litestar.exceptions import ClientException
from lib.time import MINUTES_PER_DAY

def check_duration(duration: int) -> int:
    if (duration <= 0):
        raise ClientException("Duration must be positive")
    elif (duration > MINUTES_PER_DAY):
        raise ClientException("Duration cannot exceed minutes in a day")

    return duration

MinuteDuration = Annotated[int, AfterValidator(check_duration)]
