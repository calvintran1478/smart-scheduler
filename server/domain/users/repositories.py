from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from models.user import User
from models.device import Device

class UserRepository(SQLAlchemyAsyncRepository[User]):
    """User repository"""

    model_type = User


class DeviceRepository(SQLAlchemyAsyncRepository[Device]):
    """Device repository"""

    model_type = Device