# backend/app/schemas/transaction.py
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    transaction_type: TransactionType
    category: str = Field(..., min_length=1, max_length=80)
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date
    source: Optional[str] = "manual"


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    transaction_type: Optional[TransactionType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=80)
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None
    source: Optional[str] = None


class TransactionRead(TransactionBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
