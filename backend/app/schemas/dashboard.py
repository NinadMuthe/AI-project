# backend/app/schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Optional
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
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date
    source: str = "manual"
    payment_mode: str = "UPI"
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class MonthlyCashFlow(BaseModel):
    month: str
    income: float
    expenses: float


class DailySpend(BaseModel):
    date: str
    amount: float


class DashboardSummary(BaseModel):
    total_balance: float
    total_income: float
    total_expenses: float
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    today_spend: float
    recent_transactions: List[RecentTransaction]
    expense_by_category: List[CategoryExpense]
    monthly_cash_flow: List[MonthlyCashFlow]
    daily_spending_trend: List[DailySpend]
    unreviewed_anomalies_count: int
    bank_name: Optional[str] = "HDFC Bank"
    bank_account_number: Optional[str] = None
    bank_demo_notice: str = "Bank data shown is demo data (Plaid Sandbox)"
