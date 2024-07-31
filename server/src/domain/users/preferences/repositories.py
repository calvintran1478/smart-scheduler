from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.preference import Preference

class PreferenceRepository(SQLAlchemyAsyncRepository[Preference]):
    """Preference repository"""

    model_type = Preference