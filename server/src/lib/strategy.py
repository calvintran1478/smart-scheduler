from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID
from operator import itemgetter, attrgetter
from datetime import time, date, datetime
from math import ceil

from models.schedule import Schedule
from models.preference import Preference
from models.task import Task
from lib.time import get_schedule_time_blocks, get_time_blocks, TimeBlock, SECONDS_PER_DAY

import pytz

type AssignedFocusBlock = tuple[UUID, int] # Task id, duration in seconds

class WorkStrategy(ABC):

    def get_available_time_blocks(self, schedules: Sequence[Schedule], preference: Preference, start_time: time, deadline: datetime) -> dict[Schedule, list[int]]:
        available_time_blocks = {schedule: [] for schedule in schedules}
        for schedule in schedules:
            deadline_date = deadline.date()

            if (schedule.date <= deadline_date):
                # Get unavailable time blocks based on existing schedule items and work preferences
                unavailable_time_blocks = get_schedule_time_blocks(schedule) + get_time_blocks(preference.end_of_work_day, preference.start_of_work_day)

                # In addition, mark times after the deadline as unavailable
                if (schedule.date == deadline_date):
                    unavailable_time_blocks += [(deadline.hour * 3600 + deadline.minute * 60 + deadline.second, SECONDS_PER_DAY)]

                unavailable_time_blocks.sort(key=itemgetter(0))

                # Compute available time blocks
                start = 0
                for time_block in unavailable_time_blocks:
                    end = time_block[0]
                    if (start != end):
                        available_time_blocks[schedule].append(end - start)
                    start = time_block[1]
                end = SECONDS_PER_DAY
                if (start != end):
                    available_time_blocks[schedule].append(end - start)

        return available_time_blocks

    @abstractmethod
    def execute(self, schedules: Sequence[Schedule], tasks: Sequence[Task], preference: Preference, start_time: time, timezone: pytz.timezone) -> dict[Schedule, list[AssignedFocusBlock]]:
        pass

class ChipStrategy(WorkStrategy):

    def break_down_work_time(self, required_seconds: int) -> tuple[int, int]:
        num_sessions = 1
        while ((required_seconds / num_sessions) > 90 * 60):
           num_sessions += 1
        session_length = ceil(required_seconds / num_sessions)

        return session_length, num_sessions

    def execute(self, schedules: Sequence[Schedule], tasks: Sequence[Task], preference: Preference, start_time: time, timezone: pytz.timezone) -> dict[Schedule, list[AssignedFocusBlock]]:
        """
        Strategy: Distribute work as evenly as possible across remaining available days (rounds up to the nearest time unit)
        """
        # Initialize work plan
        work_plan = {schedule: [] for schedule in schedules}

        # Get starting time for the user
        start = datetime.combine(schedules[0].date, start_time, tzinfo=timezone)

        # Plan tasks in order of priority
        sorted_tasks = sorted(tasks, key=attrgetter('deadline'))
        for task in sorted_tasks:
            # Get time range for which the task can be completed
            time_to_finish = (task.deadline - start).total_seconds()

            # Get time required to complete the task
            required_seconds = (task.time_estimate.hour * 3600 + task.time_estimate.minute * 60 + task.time_estimate.second) - (task.minutes_completed * 60)

            # Plan focus sessions for the task if needed
            if (required_seconds >= 0 and not task.done):
                # Determine how many sessions should be made for this task and how long each should be
                session_length, num_sessions = self.break_down_work_time(required_seconds)

                # Determine available times for each scheduled day
                available_time_blocks = self.get_available_time_blocks(schedules, preference, start_time, task.deadline)

                # Determine roughly how many sessions should be scheduled for each day
                num_days = (date(task.deadline.year, task.deadline.month, task.deadline.day) - schedules[0].date).days + 1
                sessions_per_day = num_sessions / num_days

                # Initialize state variables for keeping track of how many sessions need to be scheduled
                session_counter = ceil(sessions_per_day * len(schedules))
                sessions_added = 0
                schedule_index = 0
                schedules_done = []

                # Initialize variables for ensuring even distribution of focus sessions
                start_index = 0
                n = 0
                if (sessions_per_day > (1/2)):
                    n = 1
                elif ((1/3) < sessions_per_day <= (1/2)):
                    n = 2
                elif ((1/7) < sessions_per_day <= (1/3)):
                    n = 3
                else:
                    n = 7

                # Iteratively add sessions from the current date in a cyclic manner until all sessions are assigned a date (or all schedules are full)
                while (sessions_added < session_counter and len(schedules_done) < len(schedules)):
                    if (schedule_index not in schedules_done):
                        # Get available times for this schedule
                        available_times = available_time_blocks[schedules[schedule_index]]

                        # Determine the time block which has the most free time
                        max_value = max(available_times)
                        max_index = available_times.index(max_value)

                        # Add work session to the schedule if possible
                        if (session_length <= max_value):
                            work_plan[schedules[schedule_index]].append((task.id, session_length))
                            available_times[max_index] -= session_length
                            sessions_added += 1
                        else:
                            schedules_done.append(schedule_index)

                    # Determine next schedule to test for
                    schedule_index = (schedule_index + 1) % len(schedules)
                    schedule_index += n
                    if (schedule_index >= len(schedules)):
                        schedule_index = start_index
                        start_index = (start_index + 1) % n

        return work_plan
