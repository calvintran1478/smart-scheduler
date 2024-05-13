from litestar import Litestar, Router
from litestar.di import Provide
from config.plugins import plugins
from domain.users.controllers import UserController
from middleware.auth import auth_middleware, user_dependency

user_router = Router(
    path="/users",
    route_handlers=[UserController],
    dependencies={"user": Provide(user_dependency)}
)
v1_router = Router(path="/v1", route_handlers=[user_router])
router = Router(path="/api", route_handlers=[v1_router])

app = Litestar(
    route_handlers=[router],
    middleware=[auth_middleware],
    plugins=plugins
)