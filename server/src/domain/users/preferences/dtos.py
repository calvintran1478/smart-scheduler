from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.preference import Preference

class PreferenceDTO(SQLAlchemyDTO[Preference]):
    config = SQLAlchemyDTOConfig(exclude={"id", "user_id", "user", "best_focus_times.0.id", "best_focus_times.0.preference_id"})