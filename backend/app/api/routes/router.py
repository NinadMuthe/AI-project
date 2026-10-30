# backend/app/api/routes/router.py
from fastapi import APIRouter

from .auth import router as auth_router
from .transaction import router as transaction_router
from .csv_import import router as csv_import_router
from .dashboard import router as dashboard_router
from .budget import router as budget_router
from .forecast import router as forecast_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(transaction_router)
router.include_router(csv_import_router)
router.include_router(dashboard_router)
router.include_router(budget_router)
router.include_router(forecast_router)
