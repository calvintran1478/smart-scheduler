from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.repositories import UserRepository

async def provide_users_repo(db_session: AsyncSession) -> UserRepository:
    """This provides the default Users repository"""
    return UserRepository(session=db_session)