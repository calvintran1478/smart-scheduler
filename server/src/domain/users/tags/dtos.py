from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.tag import Tag

class TagDTO(SQLAlchemyDTO[Tag]):
    config = SQLAlchemyDTOConfig(include={"name", "colour"})