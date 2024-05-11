from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic.dataclasses import dataclass

from litestar import Controller, Response, post
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from litestar.datastructures import Cookie

from models.user import User
from config.settings import REFRESH_TOKEN_HOUR_LIFESPAN
from lib.token import generate_access_token, generate_refresh_token
from lib.email import normalize_email

from bcrypt import hashpw, gensalt, checkpw

@dataclass
class RegisterInput:
    email: str
    password: str
    first_name: str
    last_name: str

@dataclass
class LoginInput:
    email: str
    password: str

async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    query = select(User).where(User.email == email)
    user = await session.execute(query)
    try:
        return user.scalar_one()
    except NoResultFound as e:
        return None

class UserController(Controller):
    path = "/users"

    @post()
    async def register_user(self, data: RegisterInput, transaction: AsyncSession, done: bool | None = None) -> dict[str, str] | None:
        # Check that the email provided is valid
        normalized_email = normalize_email(data.email)
        if (normalized_email == ""):
            return Response(content={"error": "Invalid email address"}, status_code=HTTP_400_BAD_REQUEST)

        # Check if a user with the email already exists
        user = await get_user_by_email(normalized_email, transaction)
        if (user != None):
            return Response(content={"error": "User with email already exists"}, status_code=HTTP_409_CONFLICT)

        # Check that the password is sufficiently strong
        if (len(data.password) < 8):
            return Response(content={"error": "Password must be at least 8 characters long"}, status_code=HTTP_400_BAD_REQUEST)

        # Check that the first and last name fields are non-empty
        if (data.first_name == "" or data.last_name == ""):
            return Response(content={"error": "Name fields must be non-empty"}, status_code=HTTP_400_BAD_REQUEST)

        # Hash password and register user into the database
        hashed_password = hashpw(data.password.encode('utf-8'), gensalt())
        transaction.add(User(email=normalized_email, password=hashed_password.decode('utf-8'), first_name=data.first_name, last_name=data.last_name))

        return Response(content="", status_code=HTTP_201_CREATED)
    
    @post("/login")
    async def login_user(self, data: LoginInput, transaction: AsyncSession, done: bool | None = None) -> dict[str, str] | None:
        # Look up user in database
        normalized_email = normalize_email(data.email)
        user = await get_user_by_email(normalized_email, transaction)
        if (user == None):
            return Response(content={"error": "User with email not found"}, status_code=HTTP_404_NOT_FOUND)

        # Verify user password
        if not checkpw(data.password.encode('utf-8'), user.password.encode('utf-8')):
            return Response(content={"error": "Incorrect password"}, status_code=HTTP_401_UNAUTHORIZED)

        # Generate JWT for the user
        access_token = generate_access_token(normalized_email)
        refresh_token = generate_refresh_token(normalized_email)

        refresh_cookie = Cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=REFRESH_TOKEN_HOUR_LIFESPAN * 3600,
            domain="localhost",
            httponly=True,
            samesite="strict"
        )

        return Response(
            content={"access_token": access_token},
            cookies=[refresh_cookie],
            status_code=HTTP_200_OK
        )