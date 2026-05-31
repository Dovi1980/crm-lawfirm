from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.clients import router as clients_router
from app.routers.cases import router as cases_router
from app.routers.interactions import router as interactions_router
from app.routers.tasks import router as tasks_router

__all__ = [
    "auth_router",
    "users_router",
    "clients_router",
    "cases_router",
    "interactions_router",
    "tasks_router"
]
