from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from litestar.exceptions import ClientException
from email_validator import validate_email, EmailNotValidError

def check_email(email: str) -> str:
    # Check the email is valid and normalize it
    try:
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        raise ClientException(detail="Invalid email address")

def check_password_strength(password: str) -> str:
    # Check the password is at least 8 characters
    if (len(password) < 8):
        raise ClientException(detail="Password must be at least 8 characters long")

    return password

Email = Annotated[str, AfterValidator(check_email)]
Password = Annotated[str, AfterValidator(check_password_strength)]