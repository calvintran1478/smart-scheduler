from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.event import Event

class EventRepository(SQLAlchemyAsyncRepository[Event]):
    """Event repository"""

    model_type = Event