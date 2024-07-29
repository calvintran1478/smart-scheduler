from pydantic import BaseModel
from typing import Optional
from domain.users.tags.validators import TagName, TagColour

class CreateTagInput(BaseModel):
    name: TagName
    colour: TagColour

class UpdateTagInput(BaseModel):
    name: Optional[TagName] = None
    colour: Optional[TagColour] = None