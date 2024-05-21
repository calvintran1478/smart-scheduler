from litestar import Controller, Response, post, get, patch, delete
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from litestar.exceptions import ClientException, NotFoundException
from litestar.di import Provide

from models.user import User
from models.tag import Tag
from domain.users.tags.repositories import TagRepository
from domain.users.tags.dependencies import provide_tags_repo
from domain.users.tags.schemas import CreateTagInput, UpdateTagInput
from domain.users.tags.dtos import TagDTO
from domain.users.tags.hooks import after_tag_get_request

class TagController(Controller):
    dependencies = {"tags_repo": Provide(provide_tags_repo)}

    @post(path="/", return_dto=TagDTO)
    async def create_tag(self, data: CreateTagInput, user: User, tags_repo: TagRepository) -> Tag:
        # Check if user has a tag with the given name
        tag_exists = await tags_repo.exists(user_id=user.id, name=data.name)
        if tag_exists:
            raise ClientException(detail="Tag with the given name already exists", status_code=HTTP_409_CONFLICT)

        # Create tag for the user
        tag = Tag(user_id=user.id, name=data.name, colour=data.colour)
        await tags_repo.add(tag, auto_commit=True)

        return tag

    @get(path="/", return_dto=TagDTO, after_request=after_tag_get_request)
    async def get_tags(self, user: User, tags_repo: TagRepository) -> list[Tag]:
        return await tags_repo.list(user_id = user.id)

    @patch(path="/{tag_name:str}")
    async def update_tag(self, data: UpdateTagInput, user: User, tag_name: str, tags_repo: TagRepository) -> None:
        # Check if tag exists
        tag = await tags_repo.get_one_or_none(user_id=user.id, name=tag_name)
        if (tag == None):
            raise NotFoundException(detail="Tag not found")

        # Check if any other tags have the same name as the updated value
        if (data.name != None and data.name != tag.name):
            name_exists = await tags_repo.exists(user_id=user.id, name=data.name)
            if name_exists:
                raise ClientException(detail="Tag with the given name already exists", status_code=HTTP_409_CONFLICT)

        # Update tag values
        if (data.name != None):
            tag.name = data.name
        
        if (data.colour != None):
            tag.colour = data.colour

        await tags_repo.update(tag, auto_commit=True)

        return Response(content="", status_code=HTTP_204_NO_CONTENT)

    @delete(path="/{tag_name:str}")
    async def remove_tag(self, user: User, tag_name: str, tags_repo: TagRepository) -> None:
        await tags_repo.delete_by_user_id_and_tag_name(user.id, tag_name)