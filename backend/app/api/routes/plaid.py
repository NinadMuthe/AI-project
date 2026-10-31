# backend/app/api/routes/plaid.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..security import get_current_user_id
from ...services.plaid_service import auto_connect_user_bank, sync_all_items, simulate_live_indian_transaction, get_status

router = APIRouter(prefix="/plaid", tags=["plaid"])


@router.post("/connect-sandbox")
async def connect_bank_sandbox(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Ensure Plaid sandbox Indian bank account is connected and synced."""
    try:
        return await auto_connect_user_bank(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bank setup failed: {type(e).__name__}")


@router.post("/sync")
async def sync_plaid(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Trigger bank transaction refresh/sync for the current user."""
    try:
        return await sync_all_items(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {type(e).__name__}")


@router.post("/simulate-transaction")
async def simulate_purchase(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Simulate a fresh live daily purchase (e.g. Swiggy, Zomato, Blinkit)."""
    try:
        return await simulate_live_indian_transaction(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {type(e).__name__}")


@router.get("/status")
async def plaid_connection_status(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Return bank connection status for the current user (never returns access token)."""
    return await get_status(db, user_id)
