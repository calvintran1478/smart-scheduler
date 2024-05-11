from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
from models.base import Base

db_config = SQLAlchemyAsyncConfig(
    connection_string=f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    metadata=Base.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler
)

plugins=[SQLAlchemyPlugin(db_config)]