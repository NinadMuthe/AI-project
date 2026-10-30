# backend/app/api/routes/csv_import.py
# Renamed from import.py because "import" is a Python reserved keyword
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from decimal import Decimal
from sqlalchemy import select

from ..dependencies import get_db
from ...schemas.transaction import TransactionCreate
from ...services.transaction_service import create_transaction
from ...models.transaction import Transaction, TransactionType
from ..security import get_current_user_id

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_transactions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type – please upload a CSV")
    content = await file.read()
    try:
        csv_file = io.StringIO(content.decode("utf-8"))
        reader = csv.DictReader(csv_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to parse CSV")

    required_fields = {"amount", "transaction_type", "category", "transaction_date"}
    if not reader.fieldnames or not required_fields.issubset(set(reader.fieldnames)):
        raise HTTPException(status_code=400, detail="CSV must include amount, transaction_type, category, and transaction_date columns")
    imported = failed = duplicates = 0
    for line, row in enumerate(reader, start=2):
        try:
            tx_in = TransactionCreate(
                amount=Decimal(row["amount"]),
                transaction_type=row["transaction_type"],
                category=row["category"],
                merchant=row.get("merchant"),
                description=row.get("description"),
                transaction_date=row["transaction_date"],
                source="csv",
            )
            existing = await db.execute(select(Transaction.id).where(
                Transaction.user_id == user_id,
                Transaction.amount == tx_in.amount,
                Transaction.transaction_type == tx_in.transaction_type.value,
                Transaction.category == tx_in.category,
                Transaction.merchant == tx_in.merchant,
                Transaction.transaction_date == tx_in.transaction_date,
            ))
            if existing.scalar_one_or_none() is not None:
                duplicates += 1
                continue
            tx = await create_transaction(db, user_id, tx_in)
            imported += 1
        except Exception:
            failed += 1

    return {"imported": imported, "failed": failed, "duplicates": duplicates}
