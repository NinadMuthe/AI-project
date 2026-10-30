# backend/app/api/routes/plaid.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..security import get_current_user_id
from ...services.plaid_service import connect_sandbox, sync_all_items, simulate_transaction, get_status

router = APIRouter(prefix="/plaid", tags=["plaid"])


@router.post("/connect-sandbox")
async def connect_bank_sandbox(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Connect a Plaid sandbox bank account and run first sync. No Plaid Link needed."""
    try:
        result = await connect_sandbox(db, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plaid connection failed: {type(e).__name__}: {str(e)[:200]}")


@router.post("/sync")
async def sync_plaid(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Manually trigger a Plaid transaction sync for the current user."""
    try:
        result = await sync_all_items(db, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {type(e).__name__}: {str(e)[:200]}")


@router.post("/simulate-transaction")
async def simulate_purchase(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Simulate a sandbox bank transaction via webhook, then sync."""
    try:
        result = await simulate_transaction(db, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {type(e).__name__}: {str(e)[:200]}")


@router.get("/status")
async def plaid_connection_status(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Return Plaid connection status for the current user (never returns the access token)."""
    return await get_status(db, user_id)

