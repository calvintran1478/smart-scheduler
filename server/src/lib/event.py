from models.event import Event
from models.updated_event_instance import UpdatedEventInstance
from datetime import datetime
from pytz import timezone

def get_updated_event_instance_from_event(event: Event, start_time: datetime) -> UpdatedEventInstance:
    return UpdatedEventInstance(
        summary=event.summary,
        start_time=start_time,
        end_time=start_time + (event.end_time - event.start_time),
        description=event.description,
        location=event.location,
        recurrence_id=event.start_time,
        event_id=event.id
    )

def get_event_from_updated_event_instance(updated_instance: UpdatedEventInstance, timezone_format: timezone) -> Event:
    return Event(
        id=updated_instance.event_id,
        summary=updated_instance.summary,
        start_time=updated_instance.start_time.astimezone(timezone_format),
        end_time=updated_instance.end_time.astimezone(timezone_format),
        repeat_rule=updated_instance.event.repeat_rule,
        description=updated_instance.description,
        location=updated_instance.location
    )