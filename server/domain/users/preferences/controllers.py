from litestar import Controller, Response, put
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.di import Provide

from models.user import User
from models.preference import Preference
from models.preferred_time_interval import PreferredTimeInterval
from domain.users.preferences.repositories import PreferenceRepository, PreferredTimeIntervalRepository
from domain.users.preferences.dependencies import provide_preferences_repo, provide_preferred_time_interval_repo
from domain.users.preferences.schemas import SetPreferencesInput

class PreferenceController(Controller):
    dependencies = {"preferences_repo": Provide(provide_preferences_repo), "preferred_time_intervals_repo": Provide(provide_preferred_time_interval_repo)}

    @put(path="/")
    async def set_preferences(
        self,
        data: SetPreferencesInput,
        user: User,
        preferences_repo: PreferenceRepository,
        preferred_time_intervals_repo: PreferredTimeIntervalRepository,
    ) -> dict[str, str]:
        # Check existence of preference settings
        preference_result = await preferences_repo.get_one_or_none(user_id=user.id)
        preference_exists = (preference_result != None)
        time_exists = False
        if preference_exists:
            time_exists = await preferred_time_intervals_repo.exists(preference_id = preference_result.id)

        # Create new preference
        preference = Preference(
            user_id = user.id,
            wake_up_time = data.wake_up_time,
            sleep_time = data.sleep_time,
            break_length = data.break_length,
            tend_to_procrastinate = data.tend_to_procrastinate
        )

        # Update standard preferences
        if (not preference_exists):
            await preferences_repo.add(preference, auto_commit=True)
        else:
            preference.id = preference_result.id
            await preferences_repo.update(preference, auto_commit=True)

        # Delete previous focus times if any
        if preference_exists:
            await preferred_time_intervals_repo.delete_preference_times(preference_result.id)

        # Insert new preferred focus times
        best_focus_times = [PreferredTimeInterval(
            preference_id = preference.id,
            start_time = interval["start_time"],
            end_time = interval["end_time"]
        ) for interval in data.best_focus_times]

        await preferred_time_intervals_repo.add_many(best_focus_times, auto_commit=True)

        # Send appropriate response based on whether preferences were created or updated
        if (not preference_exists and not time_exists):
            preference_representation = {
                "wake_up_time": data.wake_up_time,
                "sleep_time": data.sleep_time,
                "break_length": data.break_length,
                "tend_to_procrastinate": data.tend_to_procrastinate,
                "best_focus_times": data.best_focus_times
            }
            return Response(content=preference_representation, status_code=HTTP_201_CREATED)

        return Response(content="", status_code=HTTP_204_NO_CONTENT)