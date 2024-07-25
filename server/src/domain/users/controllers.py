from litestar import Controller, post, get, patch
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.params import Parameter
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.di import Provide

from models.user import User
from domain.users.repositories import UserRepository
from domain.users.dependencies import provide_users_repo
from domain.users.schemas import RegisterInput, LoginInput, ChangePasswordInput
from domain.users.dtos import UserDTO
from middleware.auth import blacklist_store, token_family_store
from lib.token import parse_claims, TokenResponse
from config.settings import REFRESH_TOKEN_HOUR_LIFESPAN

from typing_extensions import Annotated
from datetime import datetime
from bcrypt import hashpw, gensalt, checkpw
from pytz import utc
from uuid import uuid4

class UserController(Controller):
    dependencies = {"users_repo": Provide(provide_users_repo)}

    @post(path="/", exclude_from_auth=True, return_dto=UserDTO)
    async def register_user(self, data: RegisterInput, users_repo: UserRepository) -> User:
        # Check if a user with the email already exists
        user_exists = await users_repo.exists(email = data.email)      
        if user_exists:
            raise ClientException(detail="User with email already exists", status_code=HTTP_409_CONFLICT)

        # Hash password and register user into the database
        hashed_password = hashpw(data.password.encode('utf-8'), gensalt())
        user = User(email=data.email, password=hashed_password.decode('utf-8'), first_name=data.first_name, last_name=data.last_name)
        await users_repo.add(user, auto_commit=True)

        return user

    @post(path="/login",  exclude_from_auth=True)
    async def login_user(self, data: LoginInput, users_repo: UserRepository) -> TokenResponse:
        # Look up user in database
        user = await users_repo.get_one_or_none(email=data.email)
        if (user == None):
            raise NotFoundException(detail="User with email not found")

        # Verify user password
        if not checkpw(data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise NotAuthorizedException(detail="Incorrect password")

        # Start token family
        token_family_id = uuid4()
        await token_family_store.set(str(token_family_id), 1, expires_in=REFRESH_TOKEN_HOUR_LIFESPAN * 3600)
        return TokenResponse(user.id, token_family_id, 1)

    @get(path="/token", exclude_from_auth=True)
    async def refresh_token(self, cookie: Annotated[str, Parameter(cookie="refresh-token")], users_repo: UserRepository) -> TokenResponse:
        # Get claims if token is not expired
        refresh_claims = parse_claims(cookie)

        # Check that the refresh token corresponds to a user
        user = await users_repo.get_one_or_none(id=refresh_claims["user_id"])
        if (user == None):
            raise NotAuthorizedException

        # Check that the token family exists
        expected_sequence_number = await token_family_store.get(refresh_claims["token_family_id"])
        if (expected_sequence_number == None):
            raise NotAuthorizedException

        # Check the sequence number is as expected
        if (refresh_claims["sequence_number"] != int(expected_sequence_number)):
            await token_family_store.delete(refresh_claims["token_family_id"])
            raise NotAuthorizedException

        # Update sequence number to reflect new token in the token family
        await token_family_store.set(refresh_claims["token_family_id"], refresh_claims["sequence_number"] + 1, expires_in=REFRESH_TOKEN_HOUR_LIFESPAN * 3600)
        return TokenResponse(user.id, refresh_claims["token_family_id"], refresh_claims["sequence_number"] + 1)

    @patch(path="password", status_code=HTTP_204_NO_CONTENT)
    async def change_password(self, data: ChangePasswordInput, user: User, users_repo: UserRepository) -> None:
        # Update user password
        hashed_password = hashpw(data.password.encode('utf-8'), gensalt())
        user.password = hashed_password.decode('utf-8')

        await users_repo.update(user, auto_commit=True)

    @post(path="logout", status_code=HTTP_204_NO_CONTENT)
    async def logout_user(self, cookie: Annotated[str, Parameter(cookie="refresh-token")], auth_header: Annotated[str, Parameter(header="Authorization")]) -> None:
        # Invalidate token family if refresh token is not expired
        try:
            refresh_claims = parse_claims(cookie)
            await token_family_store.delete(refresh_claims["token_family_id"])
        except NotAuthorizedException:
            pass

        # Determine remaining time for which the access token is valid
        access_token = auth_header.split()[1]
        access_claims = parse_claims(access_token)
        remaining_time = datetime.fromtimestamp(access_claims["exp"], tz=utc) - datetime.now(tz=utc)

        # Add access token to blacklist
        await blacklist_store.set(access_token, "", expires_in=remaining_time)