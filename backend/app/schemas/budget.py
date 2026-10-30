from datetime import datetime
from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=80)
    limit_amount: float = Field(..., gt=0)
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class BudgetUpdate(BaseModel):
    limit_amount: float = Field(..., gt=0)


class BudgetRead(BudgetCreate):
    id: int
    spent: float
    remaining: float
    utilization: float
    exceeded: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
