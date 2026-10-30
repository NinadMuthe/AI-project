# backend/app/ml/forecaster.py
import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import torch
import torch.nn as nn
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction
from ..schemas.forecast import DailyPoint, ForecastResponse
from ..services.model_registry import (
    get_checkpoint_path,
    update_model_status,
    should_retrain,
)


class LSTMModel(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return self.relu(out)


def create_sequences(data: np.ndarray, seq_len: int = 7) -> Tuple[torch.Tensor, torch.Tensor]:
    xs, ys = [], []
    for i in range(len(data) - seq_len):
        x = data[i : i + seq_len]
        y = data[i + seq_len]
        xs.append(x)
        ys.append(y)
    return torch.tensor(np.array(xs), dtype=torch.float32).unsqueeze(-1), torch.tensor(
        np.array(ys), dtype=torch.float32
    ).unsqueeze(-1)


async def generate_expense_forecast(
    db: AsyncSession,
    user_id: int,
    horizon_days: int = 30,
) -> ForecastResponse:
    # 1. Fetch current balances
    income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "income",
    )
    expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "expense",
    )
    total_income = float((await db.execute(income_stmt)).scalar_one())
    total_expenses = float((await db.execute(expense_stmt)).scalar_one())
    current_balance = total_income - total_expenses

    # 2. Fetch daily expenses
    tx_stmt = (
        select(
            func.date(Transaction.transaction_date).label("tx_date"),
            func.sum(Transaction.amount).label("daily_total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
        .group_by(func.date(Transaction.transaction_date))
        .order_by("tx_date")
    )
    rows = (await db.execute(tx_stmt)).all()

    # Map existing daily totals
    daily_map: Dict[date, float] = {}
    for r in rows:
        d = r.tx_date
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        daily_map[d] = float(r.daily_total)

    # If no data at all
    if not daily_map:
        update_model_status(user_id, "lstm", "not_enough_data", records_used=0, message="No expense transactions recorded.")
        return ForecastResponse(
            model_used="BASELINE (Insufficient Data)",
            is_baseline=True,
            message="No expense transactions recorded yet. Showing zero-expense baseline.",
            current_balance=round(current_balance, 2),
            projected_end_balance=round(current_balance, 2),
            shortage_flag=current_balance < 0,
            shortage_date=date.today().isoformat() if current_balance < 0 else None,
            shortage_amount=round(abs(current_balance), 2) if current_balance < 0 else None,
            shortage_warning="Account is currently in overdraft." if current_balance < 0 else None,
            series=[],
        )

    min_date = min(daily_map.keys())
    max_date = max(daily_map.keys())
    total_span_days = (max_date - min_date).days + 1

    # Fill continuous daily series
    all_dates: List[date] = []
    all_expenses: List[float] = []
    curr = min_date
    while curr <= max_date:
        all_dates.append(curr)
        all_expenses.append(daily_map.get(curr, 0.0))
        curr += timedelta(days=1)

    expense_arr = np.array(all_expenses, dtype=np.float32)
    # STEP 3 requirement: Requires at least 60 days of expense history
    MIN_DAYS_FOR_LSTM = 60
    seq_len = 7

    non_zero_days = sum(1 for v in all_expenses if v > 0)
    has_sufficient_data = total_span_days >= MIN_DAYS_FOR_LSTM and non_zero_days >= 20

    predictions: List[float] = []
    is_baseline = False
    model_name = ""
    status_message = None

    if not has_sufficient_data:
        # BASELINE FALLBACK: Never pretend LSTM was trained
        is_baseline = True
        model_name = "BASELINE (7-Day Moving Average)"
        status_message = (
            f"Insufficient history to train neural LSTM model ({total_span_days} days available, "
            f"requires >= {MIN_DAYS_FOR_LSTM} days of history). "
            "Displaying moving-average baseline projection."
        )
        update_model_status(
            user_id,
            "lstm",
            "not_enough_data",
            records_used=total_span_days,
            message=f"{total_span_days}/{MIN_DAYS_FOR_LSTM} days needed for PyTorch LSTM",
        )
        recent_window = all_expenses[-14:] if len(all_expenses) >= 14 else all_expenses
        avg_daily = float(np.mean(recent_window)) if recent_window else 50.0

        for i in range(horizon_days):
            pred_date = max_date + timedelta(days=i + 1)
            multiplier = 1.2 if pred_date.weekday() in [4, 5] else 0.95
            predictions.append(round(max(0.0, avg_daily * multiplier), 2))
    else:
        # REAL PYTORCH LSTM TRAINING & CHECKPOINT MANAGEMENT
        is_baseline = False
        model_name = "PyTorch LSTM (Trained on User Expense History)"
        status_message = (
            f"Trained PyTorch LSTM neural network on {total_span_days} days of daily expense data "
            f"({non_zero_days} active spending days)."
        )

        max_val = float(np.max(expense_arr)) if np.max(expense_arr) > 0 else 1.0
        norm_data = expense_arr / max_val
        checkpoint_path = get_checkpoint_path(user_id)

        model = LSTMModel(input_size=1, hidden_size=32, num_layers=1)
        need_train = should_retrain(user_id, "lstm", len(all_expenses)) or not checkpoint_path.exists()

        if need_train:
            update_model_status(user_id, "lstm", "training", records_used=len(all_expenses))
            X, y = create_sequences(norm_data, seq_len=seq_len)
            optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
            criterion = nn.MSELoss()

            model.train()
            for epoch in range(40):
                optimizer.zero_grad()
                out = model(X)
                loss = criterion(out, y)
                loss.backward()
                optimizer.step()

            # Save checkpoint
            torch.save({
                "model_state_dict": model.state_dict(),
                "max_val": max_val,
                "records_used": len(all_expenses),
            }, checkpoint_path)

            update_model_status(
                user_id,
                "lstm",
                "ready",
                records_used=len(all_expenses),
                message=f"Trained on {len(all_expenses)} daily records",
            )
        else:
            # Load existing checkpoint
            ckpt = torch.load(checkpoint_path, map_location="cpu")
            model.load_state_dict(ckpt["model_state_dict"])
            max_val = ckpt.get("max_val", max_val)

        # Autoregressive multi-step inference
        model.eval()
        current_seq = norm_data[-seq_len:].tolist()

        with torch.no_grad():
            for i in range(horizon_days):
                inp = torch.tensor(current_seq[-seq_len:], dtype=torch.float32).view(1, seq_len, 1)
                pred_norm = model(inp).item()
                pred_val = max(0.0, float(pred_norm * max_val))
                predictions.append(round(pred_val, 2))
                current_seq.append(pred_norm)

    # 3. Build combined series (historical + forecast) & project balance
    series_points: List[DailyPoint] = []

    # Include recent history (up to last 30 days) for visual continuity
    recent_history_slice = 30
    hist_start_idx = max(0, len(all_dates) - recent_history_slice)
    for d, exp in zip(all_dates[hist_start_idx:], all_expenses[hist_start_idx:]):
        series_points.append(
            DailyPoint(
                date=d.isoformat(),
                actual_expense=round(exp, 2),
                predicted_expense=None,
                projected_balance=None,
                is_forecast=False,
            )
        )

    # Project future balance day-by-day
    projected_bal = current_balance
    shortage_flag = False
    shortage_date = None
    shortage_amount = None

    for i, pred_exp in enumerate(predictions):
        p_date = max_date + timedelta(days=i + 1)
        projected_bal -= pred_exp

        if projected_bal < 0 and not shortage_flag:
            shortage_flag = True
            shortage_date = p_date.isoformat()
            shortage_amount = round(abs(projected_bal), 2)

        series_points.append(
            DailyPoint(
                date=p_date.isoformat(),
                actual_expense=None,
                predicted_expense=round(pred_exp, 2),
                projected_balance=round(projected_bal, 2),
                is_forecast=True,
            )
        )

    shortage_warning = None
    if shortage_flag:
        shortage_warning = (
            f"Alert: Projected cash deficit detected starting {shortage_date}. "
            f"Expected deficit reaches ${shortage_amount:.2f}. Consider reducing discretionary spending."
        )

    return ForecastResponse(
        model_used=model_name,
        is_baseline=is_baseline,
        message=status_message,
        current_balance=round(current_balance, 2),
        projected_end_balance=round(projected_bal, 2),
        shortage_flag=shortage_flag,
        shortage_date=shortage_date,
        shortage_amount=shortage_amount,
        shortage_warning=shortage_warning,
        series=series_points,
    )
