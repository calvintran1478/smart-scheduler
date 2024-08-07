from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.contrib.sqlalchemy.base import UUIDBase
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, SSL_MODE

db_config = SQLAlchemyAsyncConfig(
    connection_string=f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={SSL_MODE}",
    metadata=UUIDBase.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler
)

plugins=[SQLAlchemyPlugin(db_config)]