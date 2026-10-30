# backend/app/api/routes/anomaly.py
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..security import get_current_user_id
from ...models.transaction import Transaction
from ...schemas.anomaly import AnomalyDetectionResult, AnomalyTransactionRead
from ...ml.anomaly_detector import run_anomaly_detection

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.post("/detect", response_model=AnomalyDetectionResult)
async def trigger_detection(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    total, count, flagged = await run_anomaly_detection(db, user_id)
    return AnomalyDetectionResult(
        total_evaluated=total,
        anomalies_flagged=count,
        message=f"Isolation Forest evaluated {total} transactions and flagged {count} unusual patterns.",
        anomalies=[
            AnomalyTransactionRead(
                id=tx.id,
                user_id=tx.user_id,
                amount=float(tx.amount),
                transaction_type=tx.transaction_type,
                category=tx.category,
                merchant=tx.merchant,
                description=tx.description,
                transaction_date=tx.transaction_date.date()
                if isinstance(tx.transaction_date, datetime)
                else tx.transaction_date,
                source=tx.source,
                is_anomaly=tx.is_anomaly,
                anomaly_score=tx.anomaly_score,
                anomaly_reason=tx.anomaly_reason,
                anomaly_detected_at=tx.anomaly_detected_at,
                is_reviewed=tx.is_reviewed,
            )
            for tx in flagged
        ],
    )


@router.get("", response_model=List[AnomalyTransactionRead])
@router.get("/", response_model=List[AnomalyTransactionRead], include_in_schema=False)
async def list_anomalies(
    include_reviewed: bool = Query(True, description="Whether to include reviewed transactions"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.is_anomaly == True,
    )
    if not include_reviewed:
        stmt = stmt.where(Transaction.is_reviewed == False)

    stmt = stmt.order_by(Transaction.anomaly_detected_at.desc().nullslast(), Transaction.transaction_date.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        AnomalyTransactionRead(
            id=tx.id,
            user_id=tx.user_id,
            amount=float(tx.amount),
            transaction_type=tx.transaction_type,
            category=tx.category,
            merchant=tx.merchant,
            description=tx.description,
            transaction_date=tx.transaction_date.date()
            if isinstance(tx.transaction_date, datetime)
            else tx.transaction_date,
            source=tx.source,
            is_anomaly=tx.is_anomaly,
            anomaly_score=tx.anomaly_score,
            anomaly_reason=tx.anomaly_reason,
            anomaly_detected_at=tx.anomaly_detected_at,
            is_reviewed=tx.is_reviewed,
        )
        for tx in rows
    ]


@router.post("/{tx_id}/review", response_model=AnomalyTransactionRead)
async def mark_anomaly_reviewed(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Transaction).where(
        Transaction.id == tx_id,
        Transaction.user_id == user_id,
    )
    res = await db.execute(stmt)
    tx = res.scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx.is_reviewed = True
    await db.commit()
    await db.refresh(tx)

    return AnomalyTransactionRead(
        id=tx.id,
        user_id=tx.user_id,
        amount=float(tx.amount),
        transaction_type=tx.transaction_type,
        category=tx.category,
        merchant=tx.merchant,
        description=tx.description,
        transaction_date=tx.transaction_date.date()
        if isinstance(tx.transaction_date, datetime)
        else tx.transaction_date,
        source=tx.source,
        is_anomaly=tx.is_anomaly,
        anomaly_score=tx.anomaly_score,
        anomaly_reason=tx.anomaly_reason,
        anomaly_detected_at=tx.anomaly_detected_at,
        is_reviewed=tx.is_reviewed,
    )
