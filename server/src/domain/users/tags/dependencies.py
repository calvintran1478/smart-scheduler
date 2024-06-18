from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException
from domain.users.tags.repositories import TagRepository
from models.user import User
from models.tag import Tag

async def provide_tags_repo(db_session: AsyncSession) -> TagRepository:
    """This provides the default Tags repository"""
    return TagRepository(session=db_session)

async def provide_tag(user: User, tag_name: str, tags_repo: TagRepository) -> Tag:
    """This provides the tag belonging to the user identified by the tag name"""
    tag = await tags_repo.get_one_or_none(user_id=user.id, name=tag_name)
    if (tag == None):
        raise NotFoundException(detail="Tag not found")

    return tag