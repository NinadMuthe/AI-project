# backend/app/schemas/dashboard.py
from pydantic import BaseModel
from typing import List
from datetime import date


class CategoryExpense(BaseModel):
    category: str
    total: float

    model_config = {"from_attributes": True}


class RecentTransaction(BaseModel):
    id: int
    amount: float
    transaction_type: str
    category: str
    transaction_date: date

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    total_balance: float
    total_income: float
    total_expenses: float
    monthly_savings: float
    recent_transactions: List[RecentTransaction]
    expense_by_category: List[CategoryExpense]
    monthly_cash_flow: List["MonthlyCashFlow"]


class MonthlyCashFlow(BaseModel):
    month: str
    income: float
    expenses: float
