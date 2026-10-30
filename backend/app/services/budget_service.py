from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.budget import Budget
from ..models.transaction import Transaction, TransactionType
from ..schemas.budget import BudgetCreate, BudgetRead


async def _read(db: AsyncSession, budget: Budget) -> BudgetRead:
    start = date.fromisoformat(f"{budget.month}-01")
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    spent = (await db.execute(select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == budget.user_id, Transaction.category == budget.category,
        Transaction.transaction_type == TransactionType.EXPENSE, Transaction.transaction_date >= start,
        Transaction.transaction_date < end))).scalar_one()
    limit = float(budget.limit_amount)
    spent_amount = float(spent)
    return BudgetRead(id=budget.id, category=budget.category, limit_amount=limit, month=budget.month,
                      spent=spent_amount, remaining=limit - spent_amount,
                      utilization=round((spent_amount / limit) * 100, 2), exceeded=spent_amount > limit,
                      created_at=budget.created_at)


async def list_budgets(db: AsyncSession, user_id: int, month: str | None = None) -> list[BudgetRead]:
    query = select(Budget).where(Budget.user_id == user_id).order_by(Budget.category)
    if month:
        query = query.where(Budget.month == month)
    return [await _read(db, item) for item in (await db.execute(query)).scalars().all()]


async def create_or_update_budget(db: AsyncSession, user_id: int, data: BudgetCreate) -> BudgetRead:
    budget = (await db.execute(select(Budget).where(Budget.user_id == user_id, Budget.category == data.category, Budget.month == data.month))).scalar_one_or_none()
    if budget is None:
        budget = Budget(user_id=user_id, **data.model_dump())
        db.add(budget)
    else:
        budget.limit_amount = data.limit_amount
    await db.commit()
    await db.refresh(budget)
    return await _read(db, budget)
