# backend/app/services/context_builder.py
"""
Builds a rich financial context object for the AI assistant.
Queries the DB for user-specific data.
"""
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction


async def build_financial_context(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Build context dict with key financial metrics for current user."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    three_months_ago = now - timedelta(days=90)

    # Current month income & expenses
    curr_month_income = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
            Transaction.transaction_date >= month_start,
        )
    )).scalar_one()

    curr_month_expense = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= month_start,
        )
    )).scalar_one()

    # Total balance
    total_income = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
        )
    )).scalar_one()
    total_expense = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
    )).scalar_one()
    balance = float(total_income) - float(total_expense)

    # Top 5 expense categories (last 3 months)
    cat_rows = (await db.execute(
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= three_months_ago,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )).all()
    top_categories = [{"category": r.category, "total": float(r.total)} for r in cat_rows]

    # Recent 10 transactions
    recent_txs = (await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .limit(10)
    )).scalars().all()
    recent_list = [
        {
            "date": tx.transaction_date.strftime("%Y-%m-%d"),
            "type": tx.transaction_type,
            "category": tx.category,
            "merchant": tx.merchant or "",
            "amount": float(tx.amount),
        }
        for tx in recent_txs
    ]

    # Recent anomalies
    anomalies = (await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_anomaly == True,
            Transaction.is_reviewed == False,
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(5)
    )).scalars().all()
    anomaly_list = [
        {
            "date": tx.transaction_date.strftime("%Y-%m-%d"),
            "merchant": tx.merchant or "",
            "amount": float(tx.amount),
            "reason": tx.anomaly_reason or "",
        }
        for tx in anomalies
    ]

    return {
        "balance": round(balance, 2),
        "current_month_income": float(curr_month_income),
        "current_month_expense": float(curr_month_expense),
        "monthly_savings": round(float(curr_month_income) - float(curr_month_expense), 2),
        "top_categories": top_categories,
        "recent_transactions": recent_list,
        "unreviewed_anomalies": anomaly_list,
        "anomaly_count": len(anomaly_list),
    }

