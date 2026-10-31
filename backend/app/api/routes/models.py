# backend/app/api/routes/models.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..security import get_current_user_id
from ...services.model_registry import get_user_models_status

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/status")
async def get_models_status_route(
    user_id: int = Depends(get_current_user_id),
):
    """
    Returns the training and operational state of:
    1. PyTorch LSTM expense forecaster
    2. Scikit-learn Isolation Forest anomaly detector
    State: not_enough_data / training / ready / failed
    """
    return get_user_models_status(user_id)

