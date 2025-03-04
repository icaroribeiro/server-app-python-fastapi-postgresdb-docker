from api.components.health_check.health_check_controller import (
    HealthCheckController,
)
from api.components.user.user_controller import UserController

health_check_router = HealthCheckController()
user_router = UserController()
