from sqlalchemy.ext.asyncio import AsyncSession
from domain.users.preferences.repositories import PreferenceRepository, PreferredTimeIntervalRepository

async def provide_preferences_repo(db_session: AsyncSession) -> PreferenceRepository:
    """This provides the default Preferences repository"""
    return PreferenceRepository(session = db_session)

async def provide_preferred_time_interval_repo(db_session: AsyncSession) -> PreferredTimeIntervalRepository:
    """This provides the default PrefereredTimeIntervals repository"""
    return PreferredTimeIntervalRepository(session = db_session)