from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.repositories import UserRepository, DeviceRepository

async def provide_users_repo(db_session: AsyncSession) -> UserRepository:
    """This provides the default Users repository"""
    return UserRepository(session=db_session)

async def provide_devices_repo(db_session: AsyncSession) -> DeviceRepository:
    """This provides the default Devices repository"""
    return DeviceRepository(session=db_session)