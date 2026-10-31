# backend/app/schemas/transaction.py
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

INDIAN_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Transport",
    "Bills & Utilities",
    "Rent",
    "Shopping",
    "Entertainment",
    "Subscriptions",
    "Health",
    "Investments",
    "Education",
    "Income",
    "Others",
]

PAYMENT_MODES = [
    "UPI",
    "Card",
    "Net Banking",
    "Cash",
    "Auto-debit",
]


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: Optional[str] = "INR"
    transaction_type: TransactionType
    category: str = Field(..., min_length=1, max_length=80)
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date
    payment_mode: Optional[str] = "UPI"
    source: Optional[str] = "manual"


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=80)
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None
    payment_mode: Optional[str] = None
    source: Optional[str] = None


class TransactionRead(TransactionBase):
    id: int
    user_id: int
    plaid_transaction_id: Optional[str] = None
    pending: Optional[bool] = False
    is_anomaly: Optional[bool] = False
    anomaly_score: Optional[float] = None
    anomaly_reason: Optional[str] = None
    anomaly_detected_at: Optional[datetime] = None
    is_reviewed: Optional[bool] = False

    model_config = {"from_attributes": True}
