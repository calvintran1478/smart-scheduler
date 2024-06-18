from typing_extensions import Annotated

from litestar import Controller, post, get, patch
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.params import Parameter
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.di import Provide

from models.user import User
from models.device import Device
from domain.users.repositories import UserRepository, DeviceRepository
from domain.users.dependencies import provide_users_repo, provide_devices_repo
from domain.users.schemas import RegisterInput, LoginInput, ChangePasswordInput
from domain.users.dtos import UserDTO
from lib.token import parse_claims, TokenResponse

from bcrypt import hashpw, gensalt, checkpw

class UserController(Controller):
    dependencies = {"users_repo": Provide(provide_users_repo), "devices_repo": Provide(provide_devices_repo)}

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
    async def login_user(self, data: LoginInput, users_repo: UserRepository, devices_repo: DeviceRepository) -> TokenResponse:
        # Look up user in database
        user = await users_repo.get_one_or_none(email=data.email)
        if (user == None):
            raise NotFoundException(detail="User with email not found")

        # Verify user password
        if not checkpw(data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise NotAuthorizedException(detail="Incorrect password")

        # Log into device
        device = await devices_repo.get_one_or_none(device_id=data.device_id)
        response = TokenResponse(user.id, data.device_id, 1)
        if (device != None):
            device.refresh_token_number = 1
            await devices_repo.update(device, auto_commit=True)
        else:
            device = Device(device_id = data.device_id, user_id = user.id, refresh_token_number = 1)
            await devices_repo.add(device, auto_commit=True)

        return response

    @get(path="/token", exclude_from_auth=True)
    async def refresh_token(self, cookie: Annotated[str, Parameter(cookie="refresh-token")], users_repo: UserRepository, devices_repo: DeviceRepository) -> TokenResponse:
        # Get claims if token is not expired
        refresh_claims = parse_claims(cookie)

        # Check that the refresh token corresponds to a user
        user = await users_repo.get_one_or_none(id=refresh_claims["user_id"])
        if (user == None):
            raise NotAuthorizedException

        # Check that the device corresponds to the user
        device = await devices_repo.get_one_or_none(user_id=refresh_claims["user_id"], device_id=refresh_claims["device_id"])
        if (device == None):
            raise NotAuthorizedException

        # Check the sequence number is as expected
        if (device.refresh_token_number == None or refresh_claims["sequence_number"] != device.refresh_token_number):
            device.refresh_token_number = None
            await devices_repo.update(device, auto_commit=True)
            raise NotAuthorizedException

        device.refresh_token_number += 1
        response = TokenResponse(user.id, device.device_id, device.refresh_token_number)
        await devices_repo.update(device, auto_commit=True)

        return response

    @patch(path="password", status_code=HTTP_204_NO_CONTENT)
    async def change_password(self, data: ChangePasswordInput, user: User, users_repo: UserRepository) -> None:
        # Update user password
        hashed_password = hashpw(data.password.encode('utf-8'), gensalt())
        user.password = hashed_password.decode('utf-8')

        await users_repo.update(user, auto_commit=True)

    @post(path="logout", status_code=HTTP_204_NO_CONTENT)
    async def logout_user(self, cookie: Annotated[str, Parameter(cookie="refresh-token")], devices_repo: DeviceRepository) -> None:
        # Logout device
        refresh_claims = parse_claims(cookie)
        device = await devices_repo.get_one_or_none(device_id=refresh_claims["device_id"])
        device.refresh_token_number = None

        await devices_repo.update(device, auto_commit=True)