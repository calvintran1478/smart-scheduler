from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import delete, and_
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from models.tag import Tag

class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    """Tag repository"""

    model_type = Tag

    async def delete_by_user_id_and_tag_name(self, user_id: UUID, tag_name: str) -> None:
        try:
            await self.session.execute(statement=delete(Tag).where(and_(Tag.user_id == user_id, Tag.name == tag_name)))
        except IntegrityError:
            await self.session.rollback()
        else:
            await self.session.commit()