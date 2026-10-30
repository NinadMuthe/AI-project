# backend/app/schemas/forecast.py
from pydantic import BaseModel
from typing import List, Optional


class DailyPoint(BaseModel):
    date: str
    actual_expense: Optional[float] = None
    predicted_expense: Optional[float] = None
    projected_balance: Optional[float] = None
    is_forecast: bool = False


class ForecastResponse(BaseModel):
    model_used: str
    is_baseline: bool
    message: Optional[str] = None
    current_balance: float
    projected_end_balance: float
    shortage_flag: bool
    shortage_date: Optional[str] = None
    shortage_amount: Optional[float] = None
    shortage_warning: Optional[str] = None
    series: List[DailyPoint]
