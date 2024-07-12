from litestar import Controller, Response, put, get
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.di import Provide

from models.user import User
from models.preference import Preference
from models.preferred_time_interval import PreferredTimeInterval
from models.schedule_item import ScheduleItemTypeEnum
from domain.users.preferences.repositories import PreferenceRepository
from domain.users.preferences.dependencies import provide_preferences_repo
from domain.users.preferences.schemas import SetPreferencesInput
from domain.users.preferences.dtos import PreferenceDTO
from domain.users.schedules.repositories import ScheduleRepository
from domain.users.schedules.dependencies import provide_schedules_repo

class PreferenceController(Controller):
    dependencies = {"preferences_repo": Provide(provide_preferences_repo), "schedules_repo": Provide(provide_schedules_repo)}

    @put(path="/")
    async def set_preferences(
        self,
        data: SetPreferencesInput,
        user: User,
        preferences_repo: PreferenceRepository,
        schedules_repo: ScheduleRepository
    ) -> Response:
        # Check existence of preference settings
        preference_result = await preferences_repo.get_one_or_none(user_id=user.id)
        preference_exists = (preference_result != None)

        # Create new preference
        preference = Preference(
            user_id = user.id,
            wake_up_time = data.wake_up_time,
            sleep_time = data.sleep_time,
            start_of_work_day = data.start_of_work_day,
            end_of_work_day = data.end_of_work_day,
            break_length = data.break_length,
            tend_to_procrastinate = data.tend_to_procrastinate
        )

        # Set new preferred focus times
        preference.best_focus_times = [PreferredTimeInterval(
            start_time = interval["start_time"],
            end_time = interval["end_time"]
        ) for interval in data.best_focus_times]

        # Determine schedule items to refresh
        schedule_item_types_to_refresh = set()
        if preference_exists:
            # Calculate previous and new best focus time intervals
            previous_best_focus_times = {(preferred_interval.start_time, preferred_interval.end_time) for preferred_interval in preference_result.best_focus_times}
            new_best_focus_times = {(preferred_interval.start_time, preferred_interval.end_time) for preferred_interval in preference.best_focus_times}

            # Handle new sleeping hours
            if (preference_result.sleep_time != preference.sleep_time or preference_result.wake_up_time != preference.wake_up_time):
                schedule_item_types_to_refresh.update({
                    ScheduleItemTypeEnum.SLEEP,
                    ScheduleItemTypeEnum.HABIT
                })

            # Handle new work preferences
            work_hour_change = (preference_result.start_of_work_day != preference.start_of_work_day or preference_result.end_of_work_day != preference.end_of_work_day)
            break_length_change = (preference_result.break_length != preference.break_length)
            best_focus_time_change = (previous_best_focus_times != new_best_focus_times)
            if (work_hour_change or break_length_change or best_focus_time_change):
                schedule_item_types_to_refresh.update({
                    ScheduleItemTypeEnum.FOCUS_SESSION
                })
        else:
            schedule_item_types_to_refresh.update({
                ScheduleItemTypeEnum.SLEEP,
                ScheduleItemTypeEnum.HABIT,
                ScheduleItemTypeEnum.FOCUS_SESSION
            })

        # Update preferences
        if (preference_exists):
            preference.id = preference_result.id
            await preferences_repo.update(preference, auto_commit=True)
        else:
            await preferences_repo.add(preference, auto_commit=True)

        # Mark schedules for refresh
        await schedules_repo.mark_schedules_for_refresh(user.id, list(schedule_item_types_to_refresh))

        # Send appropriate response based on whether preferences were created or updated
        if (preference_exists):
            return Response(content="", status_code=HTTP_204_NO_CONTENT)
        else:
            preference_representation = {
                "wake_up_time": data.wake_up_time,
                "sleep_time": data.sleep_time,
                "start_of_work_day": data.start_of_work_day,
                "end_of_work_day": data.end_of_work_day,
                "break_length": data.break_length,
                "tend_to_procrastinate": data.tend_to_procrastinate,
                "best_focus_times": data.best_focus_times
            }
            return Response(content=preference_representation, status_code=HTTP_201_CREATED)

    @get(path="/", return_dto=PreferenceDTO)
    async def get_preferences(
        self,
        user: User,
        preferences_repo: PreferenceRepository
    ) -> Preference:
        # Get preferences
        preferences = await preferences_repo.get_one_or_none(user_id = user.id)
        return preferences if (preferences != None) else Preference()