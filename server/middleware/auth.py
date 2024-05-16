from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import NoResultFound

from litestar import Request
from litestar.datastructures import State
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.middleware.base import DefineMiddleware
from litestar.security.jwt import Token

from models.user import User
from models.device import Device
from lib.token import parse_claims
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        auth_header = connection.headers.get("Authorization")
        if not auth_header:
            raise NotAuthorizedException

        access_claims = parse_claims(auth_header.split()[1])
        refresh_claims = parse_claims(connection.cookies["refresh-token"])

        session_maker = async_sessionmaker()
        engine = create_async_engine(f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        async with session_maker(bind=engine) as session:
            try:
                # Get user
                user_result = await session.execute(select(User).where(User.id == access_claims["user_id"]))
                user = user_result.scalar_one()

                # Get device
                device_result = await session.execute(select(Device).where(and_(Device.user_id == user.id, Device.device_id == refresh_claims["device_id"])))
                device = device_result.scalar_one()

                # Check if device is logged in
                if (device.refresh_token_number == None):
                    raise NotAuthorizedException

            except NoResultFound:
                raise NotAuthorizedException

        return AuthenticationResult(user=user, auth=access_claims)

async def user_dependency(request: Request[User, Token, State]) -> User:
    return request.user

auth_middleware = DefineMiddleware(JWTAuthenticationMiddleware)