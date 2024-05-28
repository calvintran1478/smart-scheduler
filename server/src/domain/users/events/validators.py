from litestar.exceptions import ClientException

from models.event import Event, RepeatRuleEnum

def validate_event(event: Event) -> None:
    # Check for valid start and end times
    if (event.start_time > event.end_time):
        raise ClientException(detail="Start time must come before end time")

    # Check for valid repeat rule
    if (event.repeat_rule not in RepeatRuleEnum):
        raise ClientException(detail="Invalid repeat rule")