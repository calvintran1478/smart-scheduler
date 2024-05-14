from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from litestar import Request
from litestar.datastructures import State
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.middleware.base import DefineMiddleware
from litestar.security.jwt import Token

from models.user import User
from lib.token import parse_claims
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        auth_header = connection.headers.get("Authorization")
        if not auth_header:
            raise NotAuthorizedException

        claims = parse_claims(auth_header.split()[1])

        session_maker = async_sessionmaker()
        engine = create_async_engine(f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        async with session_maker(bind=engine) as session:
            result = await session.execute(select(User).where(User.id == claims["user_id"]))
            user = result.scalar_one()

        return AuthenticationResult(user=user, auth=claims)

async def user_dependency(request: Request[User, Token, State]) -> User:
    return request.user

auth_middleware = DefineMiddleware(JWTAuthenticationMiddleware)