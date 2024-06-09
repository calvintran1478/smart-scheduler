from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from models.event import Event
from domain.users.events.schemas import UpdateEventInput

class EventDTO(SQLAlchemyDTO[Event]):
    config = SQLAlchemyDTOConfig(exclude={"user_id", "user", "updated_event_instances", "exception_dates"}, rename_fields={"id": "event_id"})

class UpdateEventDTO(PydanticDTO[UpdateEventInput]):
    config = DTOConfig(partial=True)