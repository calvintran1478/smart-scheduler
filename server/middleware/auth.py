from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from lib.token import parse_claims

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.middleware.base import DefineMiddleware
from litestar.security.jwt import Token

class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        auth_header = connection.headers.get("Bearer")
        if not auth_header:
            raise NotAuthorizedException

        claims = parse_claims(auth_header)
        if (claims == None):
            raise NotAuthorizedException

        token = Token(**claims)

        engine = cast("AsyncEngine", connection.app.state.postgres_connection)
        async with AsyncSession(engine) as async_session:
            async with async_session.begin():
                user = await async_session.execute(select(User).where(User.id == claims["user_id"]))
        if not user:
            raise NotAuthorizedException()
        return AuthenticationResult(user=user, auth=token)

auth_middleware = DefineMiddleware(JWTAuthenticationMiddleware)