from litestar.exceptions import ClientException
from pydantic.functional_validators import AfterValidator
from pytz.exceptions import UnknownTimeZoneError
from typing_extensions import Annotated
from datetime import datetime, time
from typing import Optional
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

    new_until = convert_to_utc(update_data.timezone, datetime.combine(update_data.until, time(23, 59, 59))) \
        if (update_data.until != None) else event.until

    # Check for valid times
    if (new_start_time > new_end_time):
        raise ClientException(detail="Start time must come before end time")

    return new_start_time, new_end_time, new_until

def validate_event_query_parameters(start: Optional[str], end: Optional[str], timezone: str) -> tuple[datetime, datetime, pytz.timezone]:
    tzinfo = check_timezone(timezone.replace("-", "/"))
    start_time, end_time = None, None

    if (start != None):
        try:
            start_time = convert_to_utc(tzinfo, datetime.strptime(start, "%Y-%m-%d-%H-%M"))
        except ValueError:
            raise ClientException(detail="Invalid start date")

    if (end != None):
        try:
            end_time = convert_to_utc(tzinfo, datetime.strptime(end, "%Y-%m-%d-%H-%M"))
        except ValueError:
            raise ClientException(detail="Invalid end date")

    return start_time, end_time, tzinfo

RepeatRule = Annotated[str, AfterValidator(check_repeat_rule)]
TimeZone = Annotated[str, AfterValidator(check_timezone)]