from sqlalchemy import select

from litestar import Controller, Response, post
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from litestar.datastructures import Cookie
from litestar.di import Provide

from models.user import User
from domain.users.repositories import UserRepository
from domain.users.dependencies import provide_users_repo
from domain.users.schemas import RegisterInput, LoginInput
from lib.token import generate_access_token, generate_refresh_token
from lib.email import normalize_email
from config.settings import REFRESH_TOKEN_HOUR_LIFESPAN

from bcrypt import hashpw, gensalt, checkpw

class UserController(Controller):
    path = "/users"
    dependencies = {"users_repo": Provide(provide_users_repo)}

    @post()
    async def register_user(self, data: RegisterInput, users_repo: UserRepository) -> dict[str, str] | None:
        # Check that the email provided is valid
        normalized_email = normalize_email(data.email)
        if (normalized_email == ""):
            return Response(content={"error": "Invalid email address"}, status_code=HTTP_400_BAD_REQUEST)

        # Check if a user with the email already exists
        user = await users_repo.get_one_or_none(statement=select(User).where(User.email == normalized_email))        
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
        await users_repo.add(User(email=normalized_email, password=hashed_password.decode('utf-8'), first_name=data.first_name, last_name=data.last_name))

        return Response(content="", status_code=HTTP_201_CREATED)
    
    @post("/login")
    async def login_user(self, data: LoginInput, users_repo: UserRepository) -> dict[str, str] | None:
        # Look up user in database
        normalized_email = normalize_email(data.email)
        user = await users_repo.get_one_or_none(statement=select(User).where(User.email == normalized_email))
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