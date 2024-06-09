from pytz import utc, timezone
from datetime import datetime

def convert_to_utc(tz: timezone, dt: datetime) -> datetime:
    return tz.normalize(tz.localize(dt)).astimezone(utc)