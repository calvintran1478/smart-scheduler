from datetime import datetime
from math import floor, ceil
from copy import deepcopy
from typing import Optional, Literal
from uuid import UUID

from litestar.status_codes import HTTP_409_CONFLICT
from litestar.exceptions import ClientException

from models.schedule_item import ScheduleItem, ScheduleItemTypeEnum
from lib.time import seconds_to_time_object

# Constants
FAILURE = "FAILURE"

# Type definitions
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

    def __init__(self, name: str, duration: int) -> None:
        self.name = name
        self.duration = duration

class ConstraintSatisfactionProblem:
    variable_domains: dict[TimeVariable, Domain]
    constraints: list[Constraint]

    def __init__(self, variable_domains: dict[TimeVariable, Domain], constraints: list[Constraint]) -> None:
        self.variable_domains = variable_domains
        self.constraints = constraints

def forward_check(csp: ConstraintSatisfactionProblem, assignment: PartialSolution, var: TimeVariable, value: int) -> Failure | None:
    """Remove domain values which are inconsistent with the given assignment. If a domain becomes empty in this process a failure is returned"""
    # Determine interval numbers directly blocked by assignment
    intervals_occupied = list(range(value, value + var.duration)) 

    # Reduce unassigned variable domains based on new assignment
    unassigned_variables = [var for var in assignment.keys() if assignment[var] == None]  
    for unassigned_var in unassigned_variables:
        # Calculate new domain
        intervals_to_remove = intervals_occupied + list(range(value - unassigned_var.duration + 1, value))
        csp.variable_domains[unassigned_var] = [interval for interval in csp.variable_domains[unassigned_var] if interval not in intervals_to_remove]

        # Check if domain is empty
        if (len(csp.variable_domains[unassigned_var]) == 0):
            return FAILURE

def backtracking_search(csp: ConstraintSatisfactionProblem) -> Optional[Solution]:
    empty_solution = {k: None for k in sorted(csp.variable_domains.keys(), key=lambda var: var.duration, reverse=True)}
    return backtrack(empty_solution, csp)

def backtrack(assignment: PartialSolution, csp: ConstraintSatisfactionProblem) -> Optional[Solution]:
    # Check if assignment is complete
    if (None not in assignment.values()):
        return assignment

    # Save a copy of the domains to revert back to
    original_variable_domains = deepcopy(csp.variable_domains)

    # Select unassigned variable
    curr_var = next(var for var in assignment.keys() if assignment[var] == None)

    # Search for a valid assignment for the selected variable
    for value in csp.variable_domains[curr_var]:
        # Try variable assignment
        assignment[curr_var] = value

        # Apply forward checking to reduce variable domains
        inferences = forward_check(csp, assignment, curr_var, value)

        # If variable assignment leads to a valid solution return the result
        if (inferences != FAILURE):
            result = backtrack(assignment, csp)
            if (result != None):
                return result

        # Otherwise recover original domains to try a new variable assignment
        assignment[curr_var] = None
        csp.variable_domains = deepcopy(original_variable_domains)

def schedule_work_sessions(time_blocks: list[TimeBlock], schedule_id: UUID, session_durations: list[int], best_focus_times: list[TimeBlock]) -> list[ScheduleItem]:
    # Initalize starting domain
    num_intervals = 24 * 4
    seconds_per_interval = 60 * 15
    domain = list(range(num_intervals))
    start_intervals = []
    for time_block in time_blocks:
        # Get interval numbers that overlap with the time block
        first_interval = floor(time_block[0] / seconds_per_interval)
        last_interval = floor(time_block[1] / seconds_per_interval)
        interval_numbers = range(first_interval, last_interval + 1)

        # Reduce domain
        domain = [x for x in domain if x not in interval_numbers]

        # Track start intervals for variable specific domain reductions
        start_intervals.append(first_interval)

    # Prioritize best focus times
    for preferred_time_interval in best_focus_times:
        first_best_focus_interval = floor(preferred_time_interval[0] / seconds_per_interval)
        last_best_focus_interval = floor(preferred_time_interval[1] / seconds_per_interval)
        for interval in range(last_best_focus_interval, first_best_focus_interval - 1):
            try:
                domain.remove(interval)
                domain.insert(0, interval)
            except ValueError:
                pass

    # Create time variables
    time_variables = [TimeVariable(i, ceil(duration / seconds_per_interval)) for i, duration in enumerate(session_durations)]

    # Determine domain for each variable
    variable_domains = {}
    for time_variable in time_variables:
        intervals_to_remove = list(range(num_intervals - time_variable.duration + 1, num_intervals))
        for start_interval in start_intervals:
            intervals_to_remove += list(range(start_interval - time_variable.duration + 1, start_interval))
        variable_domains[time_variable] = [interval for interval in domain if interval not in intervals_to_remove]

    # Solve constraint satisfaction problem to produce user work sessions
    csp = ConstraintSatisfactionProblem(variable_domains, [])
    solution = backtracking_search(csp)
    if (solution != None):
        return [ScheduleItem(
            name="Work session",
            start_time=seconds_to_time_object(start_interval * seconds_per_interval),
            end_time=seconds_to_time_object((start_interval + time_variable.duration) * seconds_per_interval),
            schedule_item_type=ScheduleItemTypeEnum.FOCUS_SESSION,
            schedule_id=schedule_id
        ) for time_variable, start_interval in solution.items()]
    else:
        raise ClientException(detail="Could not find time slots for work sessions", status_code=HTTP_409_CONFLICT)