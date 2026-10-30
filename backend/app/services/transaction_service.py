# backend/app/services/transaction_service.py
from typing import List, Optional
from datetime import date
from sqlalchemy import or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.transaction import Transaction, TransactionType
from ..schemas.transaction import TransactionCreate, TransactionUpdate

async def create_transaction(db: AsyncSession, user_id: int, data: TransactionCreate) -> Transaction:
    payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    payload["transaction_type"] = payload["transaction_type"].value
    db_obj = Transaction(**payload, user_id=user_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_transaction(db: AsyncSession, user_id: int, transaction_id: int) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )
    return result.scalars().first()

async def get_transactions(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100,
                           search: str | None = None, category: str | None = None,
                           transaction_type: str | None = None, date_from: date | None = None,
                           date_to: date | None = None) -> List[Transaction]:
    statement = select(Transaction).where(Transaction.user_id == user_id)
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Transaction.category.ilike(term), Transaction.merchant.ilike(term), Transaction.description.ilike(term)))
    if category:
        statement = statement.where(Transaction.category == category)
    if transaction_type:
        statement = statement.where(Transaction.transaction_type == transaction_type)
    if date_from:
        statement = statement.where(Transaction.transaction_date >= date_from)
    if date_to:
        statement = statement.where(Transaction.transaction_date <= date_to)
    result = await db.execute(statement.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset(skip).limit(limit))
    return result.scalars().all()

async def update_transaction(db: AsyncSession, user_id: int, transaction_id: int, data: TransactionUpdate) -> Optional[Transaction]:
    payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else {k: v for k, v in data.dict().items() if v is not None}
    if "transaction_type" in payload:
        payload["transaction_type"] = payload["transaction_type"].value
    stmt = (
        update(Transaction)
        .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        .values(**{k: v for k, v in payload.items() if v is not None})
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(stmt)
    await db.commit()
    return await get_transaction(db, user_id, transaction_id)

async def delete_transaction(db: AsyncSession, user_id: int, transaction_id: int) -> bool:
    stmt = delete(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
