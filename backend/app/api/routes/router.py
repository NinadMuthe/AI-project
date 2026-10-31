# backend/app/api/routes/router.py
from fastapi import APIRouter

from .auth import router as auth_router
from .transaction import router as transaction_router
from .dashboard import router as dashboard_router
from .budget import router as budget_router
from .forecast import router as forecast_router
from .anomaly import router as anomaly_router
from .plaid import router as plaid_router
from .ocr import router as ocr_router
from .models import router as models_router
from .assistant import router as assistant_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(transaction_router)
router.include_router(dashboard_router)
router.include_router(budget_router)
router.include_router(forecast_router)
router.include_router(anomaly_router)
router.include_router(plaid_router)
router.include_router(ocr_router)
router.include_router(models_router)
router.include_router(assistant_router)
