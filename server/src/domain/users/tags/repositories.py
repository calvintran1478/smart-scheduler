from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.tag import Tag

class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    """Tag repository"""

    model_type = Tag