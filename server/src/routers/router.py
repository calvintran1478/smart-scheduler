from litestar import Router
from litestar.di import Provide
from domain.users.controllers import UserController
from domain.users.dependencies import provide_user
from domain.users.preferences.controllers import PreferenceController

preference_router = Router(path="/preferences", route_handlers=[PreferenceController])
user_router = Router(
    path="/users",
    route_handlers=[UserController, preference_router],
    dependencies={"user": Provide(provide_user)}
)
v1_router = Router(path="/v1", route_handlers=[user_router])
router = Router(path="/api", route_handlers=[v1_router])