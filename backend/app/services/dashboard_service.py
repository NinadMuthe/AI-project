# backend/app/services/dashboard_service.py
"""Dashboard aggregation utilities.
Provides summary statistics for the logged‑in user:
- total balance (income - expenses)
- total income
- total expenses
- monthly savings (income - expenses for current month)
- recent transactions (last 5)
- expense totals per category (for pie chart)
"""

from datetime import datetime
from typing import List
from sqlalchemy import select, func, desc, extract
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.transaction import Transaction, TransactionType
from ..schemas.dashboard import DashboardSummary, RecentTransaction, CategoryExpense

async def get_dashboard_summary(db: AsyncSession, user_id: int) -> DashboardSummary:
    # Total income & expenses overall
    income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.INCOME,
    )
    expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
    )
    total_income = (await db.execute(income_stmt)).scalar_one()
    total_expenses = (await db.execute(expense_stmt)).scalar_one()
    total_balance = total_income - total_expenses

    # Monthly savings for the current month
    now = datetime.utcnow()
    month_income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.INCOME,
        extract("year", Transaction.transaction_date) == now.year,
        extract("month", Transaction.transaction_date) == now.month,
    )
    month_expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        extract("year", Transaction.transaction_date) == now.year,
        extract("month", Transaction.transaction_date) == now.month,
    )
    month_income = (await db.execute(month_income_stmt)).scalar_one()
    month_expense = (await db.execute(month_expense_stmt)).scalar_one()
    monthly_savings = month_income - month_expense

    # Recent 5 transactions (most recent first)
    recent_stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.transaction_date))
        .limit(5)
    )
    recent_rows = (await db.execute(recent_stmt)).scalars().all()
    recent_transactions: List[RecentTransaction] = [
        RecentTransaction(
            id=row.id,
            amount=float(row.amount),
            transaction_type=getattr(row.transaction_type, "value", str(row.transaction_type)),
            category=row.category,
            transaction_date=row.transaction_date,
        )
        for row in recent_rows
    ]

    # Expense by category (only expense transactions)
    cat_stmt = (
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
        )
        .group_by(Transaction.category)
    )
    cat_rows = (await db.execute(cat_stmt)).all()
    expense_by_category: List[CategoryExpense] = [
        CategoryExpense(category=cat, total=float(total)) for cat, total in cat_rows
    ]

    trend_rows = (await db.execute(
        select(Transaction.transaction_date, Transaction.transaction_type, Transaction.amount)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date)
    )).all()
    grouped: dict[str, dict[str, float]] = {}
    for transaction_date, transaction_type, amount in trend_rows:
        key = transaction_date.strftime("%Y-%m")
        bucket = grouped.setdefault(key, {"income": 0.0, "expenses": 0.0})
        if transaction_type == TransactionType.INCOME:
            bucket["income"] += float(amount)
        else:
            bucket["expenses"] += float(amount)
    monthly_cash_flow = [{"month": month, **values} for month, values in grouped.items()][-12:]

    summary = DashboardSummary(
        total_balance=float(total_balance),
        total_income=float(total_income),
        total_expenses=float(total_expenses),
        monthly_savings=float(monthly_savings),
        recent_transactions=recent_transactions,
        expense_by_category=expense_by_category,
        monthly_cash_flow=monthly_cash_flow,
    )
    return summary
