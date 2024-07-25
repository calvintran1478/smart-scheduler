from pydantic import BaseModel, field_validator
from domain.users.validators import Email, Password
from litestar.exceptions import ClientException

class RegisterInput(BaseModel):
    email: Email
    password: Password
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if (v == ""):
            raise ClientException(detail="Name fields must be non-empty")
        return v

class LoginInput(BaseModel):
    email: Email
    password: str

class ChangePasswordInput(BaseModel):
    password: Password