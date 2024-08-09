from pytz import utc, timezone
from datetime import time, datetime
from math import floor

# Constants
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
SECONDS_PER_YEAR = 31536000
DAYS_PER_WEEK = 7

def convert_to_utc(tz: timezone, dt: datetime) -> datetime:
    return tz.normalize(tz.localize(dt)).astimezone(utc)

def seconds_to_time_object(seconds: int) -> time:
    hour = floor(seconds / 3600)
    if hour == 24:
        return time(23, 59, 59)
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