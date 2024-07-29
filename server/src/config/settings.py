import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Database settings
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
SSL_MODE = os.environ.get("SSL_MODE", "allow")

# Auth database settings
AUTH_DB_HOST = os.environ.get("AUTH_DB_HOST")
AUTH_DB_PORT = os.environ.get("AUTH_DB_PORT")
AUTH_DB_USER = os.environ.get("AUTH_DB_USER")
AUTH_DB_PASSWORD = os.environ.get("AUTH_DB_PASSWORD")
AUTH_TLS_ENABLED = (os.environ.get("AUTH_TLS_ENABLED") == "True")

# Token settings
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN_MINUTE_LIFESPAN = int(os.environ.get("ACCESS_TOKEN_MINUTE_LIFESPAN"))
REFRESH_TOKEN_HOUR_LIFESPAN = int(os.environ.get("REFRESH_TOKEN_HOUR_LIFESPAN"))