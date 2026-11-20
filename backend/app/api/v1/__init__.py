from fastapi import APIRouter

from app.api.v1.auth import me_router, router as auth_router
from app.api.v1.authorization import router as authorization_router
from app.api.v1.branches import router as branches_router
from app.api.v1.health import router as health_router
from app.api.v1.memberships import router as memberships_router
from app.api.v1.organizations import router as organizations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(me_router)
api_router.include_router(organizations_router)
api_router.include_router(branches_router)
api_router.include_router(memberships_router)
api_router.include_router(authorization_router)
