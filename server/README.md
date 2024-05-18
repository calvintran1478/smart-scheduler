# Getting Started

First check that Python, pip, and Postgres are installed on your system.

## Building Dependencies

Create a python virtual environment in the server directory.
```bash
python -m venv litestar-env
```
Now activate your environment with the following command.
```bash
source litestar-env/bin/activate
```
Install the package requirements using pip.
```bash
pip install -r requirements.txt
```

## Database Setup

Start Postgres if it not already running. On Linux this can be done using the command:
```bash
sudo systemctl start postgresql
```
Log into psql with the default user 'postgres'.
```bash
sudo -u postgres psql
```
Create a database for the server and give it a name.
```sql
postgres=# CREATE DATABASE <dbname>;
```
Create a user which can access and modify contents of the database. For this use the following commands with your own choice of username and password.
```sql
postgres=# CREATE USER <username> WITH ENCRYPTED PASSWORD '<password>';
postgres=# GRANT ALL PRIVILEGES ON DATABASE <dbname> TO <username>;
postgres=# \c <dbname>;
postgres=# GRANT ALL ON SCHEMA public TO <username>;
```

## Setting up Environment Variables

Move to the server/config directory and create a .env file with the following contents.
```
DB_HOST=<host>
DB_USER=<username>
DB_PASSWORD=<password>
DB_NAME=<dbname>

API_SECRET=<secret>
ACCESS_TOKEN_MINUTE_LIFESPAN=<access_token_lifespan>
REFRESH_TOKEN_HOUR_LIFESPAN=<refresh_token_lifespan>
```
For host you can simply put 'localhost'. The api secret should be a string only known by you (the one running the server), and is used for authentication. The access token minute lifespan should be set to a small value (say 10-15 minutes). The refresh token can be set for much longer (e.g. 24 hours, or even a few days).

## Starting the Server

Ensure your virtual environment is active. You can start the server by entering the following command in the server/src directory.
```bash
litestar run
```
The default port is 8000. If you wish to run the server on a different port you can use the '-p' flag as follows:
```bash
litestar run -p <port>
```
To stop the server enter Ctrl+C. To exit the virtual environment simply run the following:
```bash
deactivate
```