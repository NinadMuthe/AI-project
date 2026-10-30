# backend/app/schemas/anomaly.py
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class AnomalyTransactionRead(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str
    category: str
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date
    source: str
    is_anomaly: bool
    anomaly_score: Optional[float] = None
    anomaly_reason: Optional[str] = None
    anomaly_detected_at: Optional[datetime] = None
    is_reviewed: bool = False

    model_config = {"from_attributes": True}


class AnomalyDetectionResult(BaseModel):
    total_evaluated: int
    anomalies_flagged: int
    message: str
    anomalies: List[AnomalyTransactionRead]
