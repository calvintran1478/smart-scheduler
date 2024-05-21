import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Database settings
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

# Token settings
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN_MINUTE_LIFESPAN = int(os.environ.get("ACCESS_TOKEN_MINUTE_LIFESPAN"))
REFRESH_TOKEN_HOUR_LIFESPAN = int(os.environ.get("REFRESH_TOKEN_HOUR_LIFESPAN"))