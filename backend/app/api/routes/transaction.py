# backend/app/api/routes/transaction.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from ..dependencies import get_db
from ...schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from ...services.transaction_service import (
    create_transaction,
    get_transaction,
    get_transactions,
    update_transaction,
    delete_transaction,
)
from ...core.security import decode_access_token

from sqlalchemy.ext.asyncio import AsyncSession
from ..security import get_current_user_id

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_tx(
    tx_in: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return await create_transaction(db, user_id, tx_in)

@router.get("/", response_model=List[TransactionRead])
@router.get("", response_model=List[TransactionRead], include_in_schema=False)
async def list_txs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None, max_length=100),
    category: str | None = Query(None, max_length=80),
    transaction_type: str | None = Query(None, pattern="^(income|expense)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return await get_transactions(db, user_id, skip, limit, search, category, transaction_type, date_from, date_to)

@router.get("/{tx_id}", response_model=TransactionRead)
async def read_tx(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    tx = await get_transaction(db, user_id, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

@router.put("/{tx_id}", response_model=TransactionRead)
async def update_tx(
    tx_id: int,
    tx_in: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    tx = await update_transaction(db, user_id, tx_id, tx_in)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tx(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    success = await delete_transaction(db, user_id, tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None
