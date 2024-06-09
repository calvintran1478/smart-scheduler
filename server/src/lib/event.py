from models.event import Event
from models.updated_event_instance import UpdatedEventInstance

def get_updated_event_instance_from_event(event: Event):
    return UpdatedEventInstance(
        summary=event.summary,
        start_time=event.start_time,
        end_time=event.end_time,
        description=event.description,
        location=event.location,
        recurrence_id=event.start_time,
        event_id=event.id
    )