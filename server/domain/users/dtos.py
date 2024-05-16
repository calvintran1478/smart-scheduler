from litestar.plugins.sqlalchemy import SQLAlchemyDTO, SQLAlchemyDTOConfig

from models.user import User

class UserDTO(SQLAlchemyDTO[User]):
    config = SQLAlchemyDTOConfig(include={"email", "first_name", "last_name"})