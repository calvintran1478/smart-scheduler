from litestar.exceptions import ClientException
from pydantic.functional_validators import AfterValidator
from pytz.exceptions import UnknownTimeZoneError
from typing_extensions import Annotated
from datetime import datetime
import pytz

from models.event import Event, RepeatRuleEnum
from lib.time import convert_to_utc

def check_repeat_rule(repeat_rule: str) -> str:
    normalized_repeat_rule = repeat_rule.upper()
    if not normalized_repeat_rule in RepeatRuleEnum:
        raise ClientException(detail="Invalid repeat rule")

    return normalized_repeat_rule

def check_timezone(timezone: str) -> pytz.timezone:
    try:
        return pytz.timezone(timezone)
    except UnknownTimeZoneError:
        raise ClientException(detail="Invalid timezone")

def validate_new_times(update_data, event: Event) -> tuple[datetime, datetime]:
    # Calculate new time values
    new_start_time = convert_to_utc(update_data.timezone, update_data.start_time) \
        if (update_data.start_time != None) else event.start_time

    new_end_time = convert_to_utc(update_data.timezone, update_data.end_time) \
        if (update_data.end_time != None) else event.end_time

    # Check for valid times
    if (new_start_time > new_end_time):
        raise ClientException(detail="Start time must come before end time")

    return new_start_time, new_end_time

def validate_event_query_parameters(start: str, timezone: str) -> tuple[datetime, pytz.timezone]:
    try:
        return datetime.strptime(start, "%Y-%m-%d-%H-%M"), check_timezone(timezone.replace("-", "/"))
    except ValueError:
        raise ClientException(detail="Invalid date")

RepeatRule = Annotated[str, AfterValidator(check_repeat_rule)]
TimeZone = Annotated[str, AfterValidator(check_timezone)]