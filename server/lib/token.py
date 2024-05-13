import datetime
from uuid import UUID
from jose import JWTError, jwt
from config.settings import ACCESS_TOKEN_MINUTE_LIFESPAN, REFRESH_TOKEN_HOUR_LIFESPAN, API_SECRET
from litestar import Response
from litestar.status_codes import HTTP_200_OK
from litestar.datastructures import Cookie
from models.user import User

def generate_access_token(user_id: UUID) -> str:
    claims = {
        "authorized": True,
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_MINUTE_LIFESPAN)
    }

    return jwt.encode(claims, API_SECRET)

def generate_refresh_token(user_id: UUID, sequence_number: int) -> str:
    claims = {
        "authorized": True,
        "sequence_number": sequence_number,
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=REFRESH_TOKEN_HOUR_LIFESPAN)
    }

    return jwt.encode(claims, API_SECRET)

def parse_claims(token: str) -> dict | None:
    try:
        return jwt.decode(token, API_SECRET, algorithms=["HS256"])
    except JWTError as e:
        return None

class TokenResponse(Response):
    def __init__(self, user: User) -> None:
        access_token = generate_access_token(user.id)
        refresh_token = generate_refresh_token(user.id, user.refresh_token_number)

        refresh_cookie = Cookie(
            key="refresh-token",
            value=refresh_token,
            max_age=REFRESH_TOKEN_HOUR_LIFESPAN * 3600,
            domain="localhost",
            httponly=True,
            samesite="strict"
        )

        super().__init__(
            content={"access_token": access_token},
            cookies=[refresh_cookie],
            status_code=HTTP_200_OK
        )