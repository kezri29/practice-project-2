from fastapi import APIRouter
from app.api.routes import health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/system", tags=["system"])
# Example future routes:
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(agents.router, prefix="/ai", tags=["ai"])
