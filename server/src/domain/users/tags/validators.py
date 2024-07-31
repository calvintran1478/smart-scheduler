from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from litestar.exceptions import ClientException
from models.tag import TagColourEnum

def check_tag_name(tag_name: str) -> str:
    if (tag_name == ""):
        raise ClientException("Tag name cannot be empty")

    return tag_name

def check_tag_colour(tag_colour: str) -> str:
    normalized_tag_colour = tag_colour.lower()
    if not normalized_tag_colour in TagColourEnum:
        raise ClientException("Invalid tag colour")

    return normalized_tag_colour

TagName = Annotated[str, AfterValidator(check_tag_name)]
TagColour = Annotated[str, AfterValidator(check_tag_colour)]