from litestar import Request
from litestar.datastructures import State
from litestar.security.jwt import Token
from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.repositories import UserRepository
from models.user import User

async def provide_users_repo(db_session: AsyncSession) -> UserRepository:
    """This provides the default Users repository"""
    return UserRepository(session=db_session)

async def provide_user(request: Request[User, Token, State]) -> User:
    """This provides the user entry of the person making the request"""
    return request.user