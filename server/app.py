from litestar import Litestar, Router
from config.plugins import plugins
from domain.users.controllers import UserController
from middleware.auth import auth_middleware

v1_router = Router(path="/v1", route_handlers=[UserController])
router = Router(path="/api", route_handlers=[v1_router])

app = Litestar(
    route_handlers=[router],
    middleware=[auth_middleware],
    plugins=plugins
)