from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.schedule import Schedule

class ScheduleRepository(SQLAlchemyAsyncRepository[Schedule]):
    """Schedule repository"""

    model_type = Schedule