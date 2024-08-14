from models.schedule import Schedule
from pytz import utc, timezone
from datetime import time, datetime
from math import floor

# Constants
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
SECONDS_PER_YEAR = 31536000
MINUTES_PER_DAY = 1440
DAYS_PER_WEEK = 7
START_OF_DAY = time()
END_OF_DAY = time(23, 59, 59)

# Type definitions
type TimeBlock = tuple[float, float]

def convert_to_utc(tz: timezone, dt: datetime) -> datetime:
    return tz.normalize(tz.localize(dt)).astimezone(utc)

def seconds_to_time_object(seconds: int) -> time:
    hour = floor(seconds / 3600)
    if hour == 24:
        return END_OF_DAY
    seconds %= 3600
    minute = floor(seconds / 60)
    seconds %= 60
    second = floor(seconds)
    return time(hour=hour, minute=minute, second=second)

def get_time_difference(start_time: time, end_time: time) -> int:
    start = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    if (end_time < start_time):
        end += SECONDS_PER_DAY
    return end - start

def get_time_blocks(start_time: time, end_time: time) -> list[TimeBlock]:
    # Get second timestamps of each time object from the start of the day
    start_timestamp = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_timestamp = end_time.hour * 3600 + end_time.minute * 60 + end_time.second

    # Add 1 or 2 timeblocks depending if the time interval crosses over midnight
    time_blocks = []
    if (start_timestamp > end_timestamp):
        time_blocks.append((start_timestamp, SECONDS_PER_DAY))
        if (end_timestamp != 0):
            time_blocks.append((0, end_timestamp))
    else:
        time_blocks.append((start_timestamp, end_timestamp))

    return time_blocks

def get_time_obj_blocks(start_time: time, end_time: time) -> list[tuple[time, time]]:
    time_obj_blocks = []
    if (start_time > end_time):
        time_obj_blocks.append((start_time, END_OF_DAY))
        if (end_time != START_OF_DAY):
            time_obj_blocks.append((START_OF_DAY, end_time))
    else:
        time_obj_blocks.append((start_time, end_time))

    return time_obj_blocks

def get_schedule_time_blocks(schedule: Schedule) -> list[TimeBlock]:
    return [
        (schedule_item.start_time.hour * 3600 + schedule_item.start_time.minute * 60 + schedule_item.start_time.second,
        schedule_item.end_time.hour * 3600 + schedule_item.end_time.minute * 60 + schedule_item.end_time.second)
        for schedule_item in schedule.schedule_items
    ]