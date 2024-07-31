from litestar.exceptions import ClientException
from pydantic.functional_validators import AfterValidator
from pytz.exceptions import UnknownTimeZoneError
from typing_extensions import Annotated
import pytz

def check_timezone(timezone: str) -> pytz.timezone:
    try:
        return pytz.timezone(timezone)
    except UnknownTimeZoneError:
        raise ClientException(detail="Invalid timezone")

TimeZone = Annotated[str, AfterValidator(check_timezone)]