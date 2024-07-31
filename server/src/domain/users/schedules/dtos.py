from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.schedule import Schedule
from models.schedule_item import ScheduleItem

class ScheduleDTO(SQLAlchemyDTO[Schedule]):
    config = SQLAlchemyDTOConfig(
        include={
            "schedule_items.0.id",
            "schedule_items.0.name",
            "schedule_items.0.start_time",
            "schedule_items.0.end_time",
            "schedule_items.0.schedule_item_type"
        },
        rename_fields={"schedule_items.0.id": "schedule_item_id"}
    )

class ScheduleItemDTO(SQLAlchemyDTO[ScheduleItem]):
    config = SQLAlchemyDTOConfig(
        include={"id", "name", "start_time", "end_time", "schedule_item_type"},
        rename_fields={"id": "schedule_item_id"}
    )