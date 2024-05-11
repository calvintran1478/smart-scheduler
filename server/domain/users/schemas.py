from pydantic.dataclasses import dataclass

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