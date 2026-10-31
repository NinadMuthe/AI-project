# backend/app/services/context_builder.py
"""
Builds a rich, fresh financial context object for the AI assistant.
Always queries the live database per request for the authenticated user.
Formats all numbers into Indian Rupees (INR) with Indian digit grouping (e.g. ₹1,23,456.00).
"""
from datetime import datetime, timedelta, date
from typing import Any, Dict, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction
from ..models.plaid_item import PlaidItem


def format_inr(number: float) -> str:
    """Format float into Indian Rupee style string ₹1,23,456.00."""
    try:
        s, *d = f"{abs(number):.2f}".split(".")
        extra = f".{d[0]}" if d else ""
        if len(s) <= 3:
            formatted = f"{s}{extra}"
        else:
            last_three = s[-3:]
            remaining = s[:-3]
            out = ""
            while len(remaining) > 2:
                out = f",{remaining[-2:]}{out}"
                remaining = remaining[:-2]
            if remaining:
                out = f"{remaining}{out}"
            formatted = f"{out},{last_three}{extra}"
        sign = "-" if number < 0 else ""
        return f"{sign}₹{formatted}"
    except Exception:
        return f"₹{number:,.2f}"


async def build_financial_context(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Build context dict with fresh financial metrics for current user."""
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    ninety_days_ago = now - timedelta(days=90)

    # 1. Current month income & expenses
    curr_month_income = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
            Transaction.transaction_date >= month_start,
        )
    )).scalar_one())

    curr_month_expense = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= month_start,
        )
    )).scalar_one())

    monthly_savings = curr_month_income - curr_month_expense

    # 2. Total ledger balance
    total_income = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
        )
    )).scalar_one())

    total_expense = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
    )).scalar_one())

    balance = total_income - total_expense

    # 3. Top expense categories (last 90 days)
    cat_rows = (await db.execute(
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= ninety_days_ago,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(6)
    )).all()
    top_categories = [
        {"category": r.category, "total": float(r.total), "formatted": format_inr(float(r.total))}
        for r in cat_rows
    ]

    # 4. Top merchants (Swiggy, Zomato, Blinkit, etc.)
    mer_rows = (await db.execute(
        select(Transaction.merchant, func.sum(Transaction.amount).label("total"), func.count(Transaction.id).label("count"))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.merchant.isnot(None),
            Transaction.transaction_date >= ninety_days_ago,
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(6)
    )).all()
    top_merchants = [
        {"merchant": r.merchant, "total": float(r.total), "formatted": format_inr(float(r.total)), "count": int(r.count)}
        for r in mer_rows
    ]

    # 5. Recurring bills & subscriptions
    sub_rows = (await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.category.in_(["Subscriptions", "Bills & Utilities"]),
            Transaction.transaction_date >= month_start - timedelta(days=35),
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(8)
    )).scalars().all()
    recurring_items = [
        {"merchant": t.merchant or t.description, "amount": float(t.amount), "formatted": format_inr(float(t.amount)), "category": t.category}
        for t in sub_rows
    ]

    # 6. Recent 8 transactions
    recent_txs = (await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .limit(8)
    )).scalars().all()
    recent_list = [
        {
            "date": tx.transaction_date.strftime("%d/%m/%Y"),
            "type": tx.transaction_type,
            "category": tx.category,
            "merchant": tx.merchant or "",
            "amount": float(tx.amount),
            "formatted": format_inr(float(tx.amount)),
            "payment_mode": getattr(tx, "payment_mode", "UPI") or "UPI",
            "source": tx.source or "bank",
        }
        for tx in recent_txs
    ]

    # 7. Unreviewed unusual transactions
    anomalies = (await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_anomaly == True,
            Transaction.is_reviewed == False,
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(6)
    )).scalars().all()
    anomaly_list = [
        {
            "date": tx.transaction_date.strftime("%d/%m/%Y"),
            "merchant": tx.merchant or "",
            "amount": float(tx.amount),
            "formatted": format_inr(float(tx.amount)),
            "reason": tx.anomaly_reason or "",
        }
        for tx in anomalies
    ]

    return {
        "balance": round(balance, 2),
        "formatted_balance": format_inr(balance),
        "current_month_income": round(curr_month_income, 2),
        "formatted_current_month_income": format_inr(curr_month_income),
        "current_month_expense": round(curr_month_expense, 2),
        "formatted_current_month_expense": format_inr(curr_month_expense),
        "monthly_savings": round(monthly_savings, 2),
        "formatted_monthly_savings": format_inr(monthly_savings),
        "top_categories": top_categories,
        "top_merchants": top_merchants,
        "recurring_items": recurring_items,
        "recent_transactions": recent_list,
        "unreviewed_anomalies": anomaly_list,
        "anomaly_count": len(anomaly_list),
    }
