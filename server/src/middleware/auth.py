from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import NoResultFound

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.middleware.base import DefineMiddleware
from litestar.stores.redis import RedisStore

from models.user import User
from lib.token import parse_claims
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, SSL_MODE, \
    AUTH_DB_USER, AUTH_DB_PASSWORD, AUTH_DB_HOST, AUTH_DB_PORT, AUTH_TLS_ENABLED

valkey_store = RedisStore.with_client(url=f"{"rediss" if AUTH_TLS_ENABLED else "redis"}://{AUTH_DB_USER}:{AUTH_DB_PASSWORD}@{AUTH_DB_HOST}:{AUTH_DB_PORT}")
blacklist_store = valkey_store.with_namespace("blacklist")
token_family_store = valkey_store.with_namespace("token_family")

class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        # Check that the authorization header is included
        auth_header = connection.headers.get("Authorization")
        if not auth_header:
            raise NotAuthorizedException

        # Extract access token
        auth_header_components = auth_header.split()
        if (len(auth_header_components) != 2 or auth_header_components[0] != "Bearer"):
            raise NotAuthorizedException
        access_token = auth_header_components[1]

        # Check if the access token is blacklisted
        black_listed = await blacklist_store.exists(access_token)
        if (black_listed):
            raise NotAuthorizedException

        # Parse access token claims
        access_claims = parse_claims(access_token)

        # Get user
        session_maker = async_sessionmaker()
        engine = create_async_engine(f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={SSL_MODE}")
        async with session_maker(bind=engine) as session:
            try:
                user_result = await session.execute(select(User).where(User.id == access_claims["user_id"]))
                user = user_result.scalar_one()
            except NoResultFound:
                raise NotAuthorizedException

        return AuthenticationResult(user=user, auth=access_claims)

auth_middleware = DefineMiddleware(JWTAuthenticationMiddleware)