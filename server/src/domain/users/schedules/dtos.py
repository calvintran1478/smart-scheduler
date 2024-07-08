from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.schedule import Schedule

class ScheduleDTO(SQLAlchemyDTO[Schedule]):
    config = SQLAlchemyDTOConfig(
        include={
            "date",
            "schedule_items.0.name",
            "schedule_items.0.start_time",
            "schedule_items.0.end_time",
            "schedule_items.0.schedule_item_type"
        }
    )