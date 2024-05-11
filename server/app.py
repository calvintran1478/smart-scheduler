from litestar import Litestar, Router
from config.plugins import plugins
from lib.dependencies import dependencies
from controllers.user import UserController

v1_router = Router(path="/v1", route_handlers=[UserController])
router = Router(path="/api", route_handlers=[v1_router])

app = Litestar(
    route_handlers=[router],
    dependencies=dependencies,
    plugins=plugins
)