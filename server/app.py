from litestar import Litestar, Router
from litestar.exceptions import ClientException
from litestar.di import Provide
from config.plugins import plugins
from domain.users.controllers import UserController
from middleware.auth import auth_middleware, user_dependency
from lib.exception import client_exception_handler

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
    plugins=plugins,
    exception_handlers={ClientException: client_exception_handler}
)