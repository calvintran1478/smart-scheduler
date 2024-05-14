from sqlalchemy import select

from typing_extensions import Annotated

from litestar import Controller, Response, post, get
from litestar.status_codes import HTTP_409_CONFLICT
from litestar.params import Parameter
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.di import Provide

from models.user import User
from domain.users.repositories import UserRepository
from domain.users.dependencies import provide_users_repo
from domain.users.schemas import RegisterInput, LoginInput
from domain.users.dtos import UserDTO
from lib.token import parse_claims, TokenResponse
from lib.email import normalize_email

from bcrypt import hashpw, gensalt, checkpw

class UserController(Controller):
    dependencies = {"users_repo": Provide(provide_users_repo)}

    @post(path="/", exclude_from_auth=True, return_dto=UserDTO)
    async def register_user(self, data: RegisterInput, users_repo: UserRepository) -> User:
        # Check that the email provided is valid
        normalized_email = normalize_email(data.email)
        if (normalized_email == ""):
            raise ClientException(detail="Invalid email address")

        # Check if a user with the email already exists
        user_exists = await users_repo.exists(email = normalized_email)      
        if user_exists:
            raise ClientException(detail="User with email already exists", status_code=HTTP_409_CONFLICT)

        # Check that the password is sufficiently strong
        if (len(data.password) < 8):
            raise ClientException(detail="Password must be at least 8 characters long")

        # Check that the first and last name fields are non-empty
        if (data.first_name == "" or data.last_name == ""):
            raise ClientException(detail="Name fields must be non-empty")

        # Hash password and register user into the database
        hashed_password = hashpw(data.password.encode('utf-8'), gensalt())
        user = User(email=normalized_email, password=hashed_password.decode('utf-8'), first_name=data.first_name, last_name=data.last_name)
        await users_repo.add(user, auto_commit=True)

        return user

    @post(path="/login",  exclude_from_auth=True)
    async def login_user(self, data: LoginInput, users_repo: UserRepository) -> TokenResponse:
        # Look up user in database
        normalized_email = normalize_email(data.email)
        user = await users_repo.get_one_or_none(statement=select(User).where(User.email == normalized_email))
        if (user == None):
            raise NotFoundException(detail="User with email not found")

        # Verify user password
        if not checkpw(data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise NotAuthorizedException(detail="Incorrect password")

        user.refresh_token_number = 1
        await users_repo.update(user, auto_commit=True)

        return TokenResponse(user)

    @get(path="/token", exclude_from_auth=True)
    async def refresh_token(self, cookie: Annotated[str, Parameter(cookie="refresh-token")], users_repo: UserRepository) -> TokenResponse:
        # Get claims if token is not expired
        claims = parse_claims(cookie)

        # Check that the refresh token corresponds to a user
        user = await users_repo.get_one_or_none(statement=select(User).where(User.id == claims["user_id"]))
        if (user == None):
            raise NotAuthorizedException

        # Check the sequence number is as expected
        if (user.refresh_token_number == None or claims["sequence_number"] != user.refresh_token_number):
            user.refresh_token_number = None
            await users_repo.update(user, auto_commit=True)
            raise NotAuthorizedException

        user.refresh_token_number += 1
        await users_repo.update(user, auto_commit=True)

        return TokenResponse(user)