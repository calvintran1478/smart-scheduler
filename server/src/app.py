from litestar import Litestar
from config.cors import cors_config
from config.plugins import plugins
from middleware.auth import auth_middleware
from lib.exception import exception_handlers
from routers.router import router

app = Litestar(
    route_handlers=[router],
    middleware=[auth_middleware],
    cors_config=cors_config,
    plugins=plugins,
    exception_handlers=exception_handlers
)