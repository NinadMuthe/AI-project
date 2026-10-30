# backend/app/api/routes/forecast.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..security import get_current_user_id
from ...schemas.forecast import ForecastResponse
from ...ml.forecaster import generate_expense_forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("", response_model=ForecastResponse)
@router.get("/", response_model=ForecastResponse, include_in_schema=False)
async def get_forecast(
    horizon: int = Query(30, ge=15, le=90, description="Forecast horizon in days (15-90)"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return await generate_expense_forecast(db, user_id=user_id, horizon_days=horizon)
