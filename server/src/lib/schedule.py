from lib.constraint import TimeBlock
from datetime import time

def get_time_blocks(start_time: time, end_time: time) -> list[TimeBlock]:
    # Get second timestamps of each time object from the start of the day
    start_timestamp = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_timestamp = end_time.hour * 3600 + end_time.minute * 60 + end_time.second

    # Add 1 or 2 timeblocks depending if the time interval crosses over midnight
    time_blocks = []
    if (start_timestamp > end_timestamp):
        time_blocks.append((start_timestamp, 24 * 3600))
        if (end_timestamp != 0):
            time_blocks.append((0, end_timestamp))
    else:
        time_blocks.append((start_timestamp, end_timestamp))

    return time_blocks