from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.event import Event

class CreateEventDTO(SQLAlchemyDTO[Event]):
    config = SQLAlchemyDTOConfig(exclude={"id", "user_id", "user"})

class UpdateEventDTO(SQLAlchemyDTO[Event]):
    config = SQLAlchemyDTOConfig(exclude={"id", "user_id", "user"}, partial=True)

class ReadEventDTO(SQLAlchemyDTO[Event]):
    config = SQLAlchemyDTOConfig(exclude={"user_id", "user"}, rename_fields={"id": "event_id"})