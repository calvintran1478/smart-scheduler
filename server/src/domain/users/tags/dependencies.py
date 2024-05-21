from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.tags.repositories import TagRepository

async def provide_tags_repo(db_session: AsyncSession) -> TagRepository:
    """This provides the default Tags repository"""
    return TagRepository(session=db_session)