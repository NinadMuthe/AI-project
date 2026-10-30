# backend/app/api/routes/sample_data.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..security import get_current_user_id
from ...services.sample_data_service import has_sample_data, load_sample_data
from ...ml.anomaly_detector import run_anomaly_detection

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/load-sample", status_code=status.HTTP_201_CREATED)
async def load_sample(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Generate ~6 months of realistic synthetic transactions for the logged-in user.
    Returns 409 if sample data has already been loaded for this user.
    Triggers anomaly detection in background after inserting.
    """
    if await has_sample_data(db, user_id):
        raise HTTPException(
            status_code=409,
            detail="Sample data has already been loaded for your account. Each account can only load sample data once.",
        )

    inserted = await load_sample_data(db, user_id)

    # Run anomaly detection in background (non-blocking)
    async def _run_anomaly():
        async with AsyncSession(db.bind) as bg_db:
            await run_anomaly_detection(bg_db, user_id)

    background_tasks.add_task(run_anomaly_detection, db, user_id)

    return {
        "inserted": inserted,
        "message": f"Loaded {inserted} sample transactions covering approximately 6 months of financial history.",
    }

