from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_db
from ..security import get_current_user_id
from ...models.budget import Budget
from ...schemas.budget import BudgetCreate, BudgetRead
from ...services.budget_service import create_or_update_budget, list_budgets

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.get("", response_model=list[BudgetRead])
async def list_items(month: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return await list_budgets(db, user_id, month)

@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def save_item(data: BudgetCreate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return await create_or_update_budget(db, user_id, data)

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(budget_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    result = await db.execute(delete(Budget).where(Budget.id == budget_id, Budget.user_id == user_id))
    await db.commit()
    if not result.rowcount:
        raise HTTPException(status_code=404, detail="Budget not found")
