from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.exceptions import HTTPException
from models.preference import Preference
from models.preferred_time_interval import PreferredTimeInterval
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from uuid import UUID

class PreferenceRepository(SQLAlchemyAsyncRepository[Preference]):
    """Preference repository"""

    model_type = Preference


class PreferredTimeIntervalRepository(SQLAlchemyAsyncRepository[PreferredTimeInterval]):
    """Preferred Time Interval repository"""

    model_type = PreferredTimeInterval

    async def delete_preference_times(self, preference_id: UUID) -> None:
        try:
            await self.session.execute(statement=delete(PreferredTimeInterval).where(PreferredTimeInterval.preference_id == preference_id))
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException
        else:
            await self.session.commit()