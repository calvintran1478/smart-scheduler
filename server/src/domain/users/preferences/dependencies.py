from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.preferences.repositories import PreferenceRepository

async def provide_preferences_repo(db_session: AsyncSession) -> PreferenceRepository:
    """This provides the default Preferences repository"""
    return PreferenceRepository(session = db_session)