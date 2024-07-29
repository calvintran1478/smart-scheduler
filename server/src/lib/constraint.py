from datetime import datetime, time
from math import floor, ceil
from typing import Optional, Literal, Generator
from uuid import UUID
from itertools import chain

from litestar.status_codes import HTTP_409_CONFLICT
from litestar.exceptions import ClientException

from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from lib.time import seconds_to_time_object

# Constants
SECONDS_PER_DAY = 86400
DAYS_PER_WEEK = 7
FAILURE = "FAILURE"

# Type definitions
type ScheduleItemDetails = tuple[str, int, ScheduleItemTypeEnum] # name, duration (in seconds), schedule item type
type TimeBlock = tuple[float, float]
type Domain = list[int]
type Relation = callable[[dict[TimeVariable, int]], bool]
type Constraint = tuple[list[TimeVariable], Relation]
type PartialSolution = dict[TimeVariable, int | None]
type Solution = dict[TimeVariable, int]
type Failure = Literal[FAILURE]

class TimeVariable:
    name: str
    duration: int # in multiples of 15 minutes
    schedule_item_type: ScheduleItemTypeEnum
    num_preferred_intervals_available: int

    def __init__(self, name: str, duration: int, schedule_item_type: ScheduleItemTypeEnum, num_preferred_intervals_available: int = 0) -> None:
        self.name = name
        self.duration = duration
        self.schedule_item_type = schedule_item_type
        self.num_preferred_intervals_available = num_preferred_intervals_available

class ConstraintSatisfactionProblem:
    variable_domains: dict[TimeVariable, Domain]
    constraints: list[Constraint]

    def __init__(self, variable_domains: dict[TimeVariable, Domain], constraints: list[Constraint]) -> None:
        self.variable_domains = variable_domains
        self.constraints = constraints

def forward_check(csp: ConstraintSatisfactionProblem, assignment: PartialSolution, assigned_var: TimeVariable, value: int, preferred_value_spacing: int) -> Failure | None:
    """Remove domain values which are inconsistent with the given assignment. If a domain becomes empty in this process a failure is returned"""
    # Determine interval numbers directly blocked by assignment
    intervals_occupied = range(value, value + assigned_var.duration)

    # Reduce unassigned variable domains based on new assignment
    unassigned_variables = (var for var in assignment.keys() if assignment[var] == None)
    for unassigned_var in unassigned_variables:
        # Calculate new domain
        csp.variable_domains[unassigned_var] = [interval for interval in csp.variable_domains[unassigned_var] if interval not in intervals_occupied]
        csp.variable_domains[unassigned_var] = [interval for interval in csp.variable_domains[unassigned_var] if interval not in range(value - unassigned_var.duration + 1, value)]

        # Check if domain is empty
        if (len(csp.variable_domains[unassigned_var]) == 0):
            return FAILURE

        # Prioritize values away from the new assignment based on the preferred spacing
        first_interval = value
        last_interval = first_interval + assigned_var.duration - 1
        intervals_to_shift = chain(range(first_interval - preferred_value_spacing, first_interval), range(last_interval + 1, last_interval + 1 + preferred_value_spacing))
        for interval in intervals_to_shift:
            try:
                csp.variable_domains[unassigned_var].remove(interval)
                csp.variable_domains[unassigned_var].append(interval)
            except ValueError:
                pass

def backtracking_search(csp: ConstraintSatisfactionProblem, preferred_value_spacing: int) -> Optional[Solution]:
    empty_solution = {k: None for k in sorted(csp.variable_domains.keys(), key=lambda var: (var.duration, -var.num_preferred_intervals_available), reverse=True)}
    return backtrack(csp, empty_solution, preferred_value_spacing)

def backtrack(csp: ConstraintSatisfactionProblem, assignment: PartialSolution, preferred_value_spacing: int) -> Optional[Solution]:
    # Check if assignment is complete
    if (None not in assignment.values()):
        return assignment

    # Select unassigned variable
    curr_var = next(var for var in assignment.keys() if assignment[var] == None)

    # Save a copy of the domains to revert back to
    original_variable_domains = {k: tuple(v) for k, v in csp.variable_domains.items() if assignment[k] == None and k != curr_var}

    # Search for a valid assignment for the selected variable
    for value in csp.variable_domains[curr_var]:
        # Try variable assignment
        assignment[curr_var] = value

        # Apply forward checking to reduce variable domains
        inferences = forward_check(csp, assignment, curr_var, value, preferred_value_spacing)

        # If variable assignment leads to a valid solution return the result
        if (inferences != FAILURE):
            result = backtrack(csp, assignment, preferred_value_spacing)
            if (result != None):
                return result

        # Otherwise recover original domains to try a new variable assignment
        assignment[curr_var] = None
        for k, v in original_variable_domains.items():
            csp.variable_domains[k] = list(v)

def schedule_daily_items(time_blocks: list[TimeBlock], daily_items: list[ScheduleItemDetails], preferred_times: list[list[TimeBlock]], preferred_spacing: int) -> list[ScheduleItem]:    
    # Initialize starting domain
    seconds_per_interval = 60 * 15
    num_intervals = floor(86400 / seconds_per_interval)
    domain = range(num_intervals)
    start_intervals = []
    for time_block in time_blocks:
        # Get interval numbers that overlap with the time block
        first_interval = floor(time_block[0] / seconds_per_interval)
        result = time_block[1] / seconds_per_interval
        last_interval = result - 1 if result.is_integer() else floor(result)
        interval_numbers = range(first_interval, int(last_interval) + 1)

        # Reduce domain
        domain = tuple(x for x in domain if x not in interval_numbers)

        # Track start intervals for variable specific domain reductions
        start_intervals.append(first_interval)

    # Create time variables
    time_variables = tuple(TimeVariable(name, ceil(duration / seconds_per_interval), schedule_item_type) for name, duration, schedule_item_type in daily_items)

    # Determine domain for each variable
    variable_domains = {}
    for i, time_variable in enumerate(time_variables):
        # Reduce domain to viable values
        variable_domains[time_variable] = [x for x in domain if x not in range(num_intervals - time_variable.duration + 1, num_intervals)]
        for start_interval in start_intervals:
            variable_domains[time_variable] = [x for x in variable_domains[time_variable] if x not in range(start_interval - time_variable.duration + 1, start_interval)]

        # Prioritize values
        for preferred_time_interval in preferred_times[i]:
            first_preferred_interval = floor(preferred_time_interval[0] / seconds_per_interval)
            result = preferred_time_interval[1] / seconds_per_interval
            last_preferred_interval = result - 1 if result.is_integer() else floor(result)
            for interval in range(int(last_preferred_interval), first_preferred_interval - 1, -1):
                try:
                    variable_domains[time_variable].remove(interval)
                    variable_domains[time_variable].insert(0, interval)
                    time_variable.num_preferred_intervals_available += 1
                except ValueError:
                    pass

    # Solve constraint satisfaction problem to produce a schedule for the given daily items
    csp = ConstraintSatisfactionProblem(variable_domains, [])
    preferred_value_spacing = ceil(preferred_spacing / seconds_per_interval)
    solution = backtracking_search(csp, preferred_value_spacing)
    if (solution != None):
        return [ScheduleItem(
            name=time_variable.name,
            start_time=seconds_to_time_object(start_interval * seconds_per_interval),
            end_time=seconds_to_time_object((start_interval + time_variable.duration) * seconds_per_interval),
            schedule_item_type=time_variable.schedule_item_type,
        ) for time_variable, start_interval in solution.items()]
    else:
        raise ClientException(detail="Could not find time slots for daily items", status_code=HTTP_409_CONFLICT)

def schedule_weekly_items(time_blocks: list[TimeBlock], weekly_items: list[ScheduleItemDetails], preferred_times: list[list[TimeBlock]], preferred_spacing: int) -> list[list[ScheduleItem]]:
    # Initialize starting domain
    seconds_per_interval = 60 * 15
    num_intervals = floor(SECONDS_PER_DAY * DAYS_PER_WEEK / seconds_per_interval)
    domain = range(num_intervals)
    start_intervals = []
    for time_block in time_blocks:
        # Get interval numbers that overlap with the time block
        first_interval = floor(time_block[0] / seconds_per_interval)
        result = time_block[1] / seconds_per_interval
        last_interval = result - 1 if result.is_integer() else floor(result)
        interval_numbers = range(first_interval, int(last_interval) + 1)

        # Reduce domain
        domain = tuple(x for x in domain if x not in interval_numbers)

        # Track start intervals for variable specific domain reductions
        start_intervals.append(first_interval)

    # Create time variables
    time_variables = tuple(TimeVariable(name, ceil(duration / seconds_per_interval), schedule_item_type) for name, duration, schedule_item_type in weekly_items)

    # Determine domain for each variable
    variable_domains = {}
    for i, time_variable in enumerate(time_variables):
        # Reduce domain to viable values
        variable_domains[time_variable] = [x for x in domain if x not in range(num_intervals - time_variable.duration + 1, num_intervals)]
        for start_interval in start_intervals:
            variable_domains[time_variable] = [x for x in variable_domains[time_variable] if x not in range(start_interval - time_variable.duration + 1, start_interval)]

        # Prioritize values
        for preferred_time_interval in preferred_times[i]:
            first_preferred_interval = floor(preferred_time_interval[0] / seconds_per_interval)
            result = preferred_time_interval[1] / seconds_per_interval
            last_preferred_interval = result - 1 if result.is_integer() else floor(result)
            for interval in range(int(last_preferred_interval), first_preferred_interval - 1, -1):
                try:
                    variable_domains[time_variable].remove(interval)
                    variable_domains[time_variable].insert(0, interval)
                    time_variable.num_preferred_intervals_available += 1
                except ValueError:
                    pass

    # Solve constraint satisfaction problem to produce a schedule for the given weekly items
    csp = ConstraintSatisfactionProblem(variable_domains, [])
    preferred_value_spacing = ceil(preferred_spacing / seconds_per_interval)
    solution = backtracking_search(csp, preferred_value_spacing)
    if (solution != None):
        schedule_items = [[] for _ in range(DAYS_PER_WEEK)]
        for time_variable, start_interval in solution.items():
            # Second offset of schedule item from start of the first day
            start = start_interval * seconds_per_interval
            end = (start_interval + time_variable.duration) * seconds_per_interval

            # Start and end days of the schedule item
            start_day = floor(start / SECONDS_PER_DAY)
            end_day = floor(end / SECONDS_PER_DAY)

            # Second offset of the schedule item from its respective start and end days
            start_day_offset = start % SECONDS_PER_DAY
            end_day_offset = end % SECONDS_PER_DAY

            # Schedule item is contained within a single day
            if (start_day == end_day):
                schedule_items[start_day].append(ScheduleItem(
                    name=time_variable.name,
                    start_time=seconds_to_time_object(start_day_offset),
                    end_time=seconds_to_time_object(end_day_offset),
                    schedule_item_type=time_variable.schedule_item_type
                ))

            # Schedule item occurs over multiple days
            elif (start_day < end_day):
                # First day
                schedule_items[start_day].append(ScheduleItem(
                    name=time_variable.name,
                    start_time=seconds_to_time_object(start_offset),
                    end_time=seconds_to_time_object(SECONDS_PER_DAY),
                    schedule_item_type=time_variable.schedule_item_type
                ))

                # Middle days
                day = start_day + 1
                while (day < end_day):
                    schedule_items[day].append(ScheduleItem(
                        name=time_variable.name,
                        start_time=time(),
                        end_time=seconds_to_time_object(SECONDS_PER_DAY),
                        schedule_item_type=time_variable.schedule_item_type
                    ))
                    day += 1

                # Last day
                if (end_offset != 0):
                    schedule_items[end_day].append(ScheduleItem(
                        name=time_variable.name,
                        start_time=time(),
                        end_time=seconds_to_time_object(end_offset),
                        schedule_item_type=time_variable.schedule_item_type
                    ))

        return schedule_items
    else:
        raise ClientException(detail="Could not find time slots for weekly items", status_code=HTTP_409_CONFLICT)