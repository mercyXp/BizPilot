from fastapi import APIRouter

from app.api.v1.accounting import router as accounting_router
from app.api.v1.auth import router as auth_router
from app.api.v1.authorization import router as authorization_router
from app.api.v1.branches import router as branches_router
from app.api.v1.catalogue import router as catalogue_router
from app.api.v1.customers import router as customers_router
from app.api.v1.demo import router as demo_router
from app.api.v1.health import router as health_router
from app.api.v1.i18n import router as i18n_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.memberships import router as memberships_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.payroll import router as payroll_router
from app.api.v1.pos import router as pos_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.purchasing import router as purchasing_router
from app.api.v1.sales import router as sales_router
from app.api.v1.warehouses import router as warehouses_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(i18n_router)
api_router.include_router(auth_router)
api_router.include_router(demo_router)
api_router.include_router(organizations_router)
api_router.include_router(branches_router)
api_router.include_router(warehouses_router)
api_router.include_router(memberships_router)
api_router.include_router(invitations_router)
api_router.include_router(authorization_router)
api_router.include_router(catalogue_router)
api_router.include_router(inventory_router)
api_router.include_router(customers_router)
api_router.include_router(pos_router)
api_router.include_router(sales_router)
api_router.include_router(purchasing_router)
api_router.include_router(accounting_router)
api_router.include_router(payroll_router)
api_router.include_router(reporting_router)
