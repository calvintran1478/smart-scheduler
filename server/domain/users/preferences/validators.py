from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from litestar.exceptions import ClientException
from datetime import datetime, time

def check_focus_times(focus_times: list[str]) -> list[list[time]]:
    try:
        start_end_times = [interval.split(" - ") for interval in focus_times]
        return [
            {
                "start_time": datetime.strptime(interval[0], '%H:%M:%S').time(),
                "end_time": datetime.strptime(interval[1], '%H:%M:%S').time()
            }
            for interval in start_end_times]
    except ValueError:
        raise ClientException("Invalid format for best focus times")

FocusTimes = Annotated[list[str], AfterValidator(check_focus_times)]