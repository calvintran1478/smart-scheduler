from jwt import encode
import datetime
from config.settings import ACCESS_TOKEN_MINUTE_LIFESPAN, REFRESH_TOKEN_HOUR_LIFESPAN, API_SECRET

def generate_access_token(user_email: str) -> str:
    claims = {
        "authorized": True,
        "email": user_email,
        "exp": datetime.datetime.now() + datetime.timedelta(minutes=ACCESS_TOKEN_MINUTE_LIFESPAN)
    }

    return encode(claims, API_SECRET)

def generate_refresh_token(user_email: str) -> str:
    token_life_span = 15

    claims = {
        "authorized": True,
        "email": user_email,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=REFRESH_TOKEN_HOUR_LIFESPAN)
    }

    return encode(claims, API_SECRET)