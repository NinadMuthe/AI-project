# backend/app/services/dashboard_service.py
"""Dashboard aggregation utilities for Indian Daily Expense Manager."""

from datetime import datetime, date
from typing import List
from sqlalchemy import select, func, desc, extract
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.transaction import Transaction
from ..models.plaid_item import PlaidItem
from ..schemas.dashboard import (
    DashboardSummary,
    RecentTransaction,
    CategoryExpense,
    MonthlyCashFlow,
    DailySpend,
)

async def get_dashboard_summary(db: AsyncSession, user_id: int) -> DashboardSummary:
    now = datetime.now()
    today_date = date.today()

    # 1. Total income & expenses overall
    income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "income",
    )
    expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "expense",
    )
    total_income = float((await db.execute(income_stmt)).scalar_one())
    total_expenses = float((await db.execute(expense_stmt)).scalar_one())
    total_balance = total_income - total_expenses

    # 2. Monthly income & expenses for the current month
    month_income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "income",
        extract("year", Transaction.transaction_date) == now.year,
        extract("month", Transaction.transaction_date) == now.month,
    )
    month_expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "expense",
        extract("year", Transaction.transaction_date) == now.year,
        extract("month", Transaction.transaction_date) == now.month,
    )
    monthly_income = float((await db.execute(month_income_stmt)).scalar_one())
    monthly_expenses = float((await db.execute(month_expense_stmt)).scalar_one())
    monthly_savings = monthly_income - monthly_expenses

    # 3. Today's spend
    today_spend_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "expense",
        func.date(Transaction.transaction_date) == today_date,
    )
    today_spend = float((await db.execute(today_spend_stmt)).scalar_one())

    # 4. Recent transactions (last 6, most recent first)
    recent_stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.transaction_date), desc(Transaction.id))
        .limit(6)
    )
    recent_rows = (await db.execute(recent_stmt)).scalars().all()
    recent_transactions: List[RecentTransaction] = [
        RecentTransaction(
            id=row.id,
            amount=float(row.amount),
            transaction_type=row.transaction_type,
            category=row.category,
            merchant=row.merchant,
            description=row.description,
            transaction_date=row.transaction_date.date() if isinstance(row.transaction_date, datetime) else row.transaction_date,
            source=row.source or "manual",
            payment_mode=getattr(row, "payment_mode", "UPI") or "UPI",
            is_anomaly=bool(getattr(row, "is_anomaly", False)),
            anomaly_reason=getattr(row, "anomaly_reason", None),
        )
        for row in recent_rows
    ]

    # 5. Expense by category (past 90 days or all)
    cat_stmt = (
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
        .group_by(Transaction.category)
        .order_by(desc(func.coalesce(func.sum(Transaction.amount), 0)))
    )
    cat_rows = (await db.execute(cat_stmt)).all()
    expense_by_category: List[CategoryExpense] = [
        CategoryExpense(category=cat, total=float(total)) for cat, total in cat_rows
    ]

    # 6. Monthly Cash Flow (last 6 months)
    trend_rows = (await db.execute(
        select(Transaction.transaction_date, Transaction.transaction_type, Transaction.amount)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date)
    )).all()
    grouped: dict[str, dict[str, float]] = {}
    for transaction_date, transaction_type, amount in trend_rows:
        key = transaction_date.strftime("%Y-%m")
        bucket = grouped.setdefault(key, {"income": 0.0, "expenses": 0.0})
        t_type = str(transaction_type).lower()
        if t_type == "income":
            bucket["income"] += float(amount)
        else:
            bucket["expenses"] += float(amount)
    monthly_cash_flow = [MonthlyCashFlow(month=m, **v) for m, v in grouped.items()][-6:]

    # 7. Daily spending trend for the current month
    daily_stmt = (
        select(func.date(Transaction.transaction_date), func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            extract("year", Transaction.transaction_date) == now.year,
            extract("month", Transaction.transaction_date) == now.month,
        )
        .group_by(func.date(Transaction.transaction_date))
        .order_by(func.date(Transaction.transaction_date))
    )
    daily_rows = (await db.execute(daily_stmt)).all()
    daily_spending_trend = [
        DailySpend(date=d.strftime("%d/%m") if hasattr(d, "strftime") else str(d), amount=float(amt))
        for d, amt in daily_rows
    ]

    # 8. Unreviewed anomalies count
    anom_stmt = select(func.count(Transaction.id)).where(
        Transaction.user_id == user_id,
        Transaction.is_anomaly == True,
        Transaction.is_reviewed == False,
    )
    unreviewed_anomalies_count = int((await db.execute(anom_stmt)).scalar_one() or 0)

    # 9. Plaid bank info
    plaid_item = (await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user_id, PlaidItem.status == "active")
    )).scalars().first()
    bank_name = plaid_item.institution_name if plaid_item else "HDFC Bank (Sandbox)"

    return DashboardSummary(
        total_balance=round(total_balance, 2),
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        monthly_income=round(monthly_income, 2),
        monthly_expenses=round(monthly_expenses, 2),
        monthly_savings=round(monthly_savings, 2),
        today_spend=round(today_spend, 2),
        recent_transactions=recent_transactions,
        expense_by_category=expense_by_category,
        monthly_cash_flow=monthly_cash_flow,
        daily_spending_trend=daily_spending_trend,
        unreviewed_anomalies_count=unreviewed_anomalies_count,
        bank_name=bank_name,
        bank_demo_notice="Bank data shown is demo data (Plaid Sandbox)",
    )
