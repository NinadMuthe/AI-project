# backend/app/ml/anomaly_detector.py
from datetime import datetime, date
from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction
from ..services.model_registry import update_model_status

INDIAN_CATEGORIES_LIST = [
    "Food & Dining", "Groceries", "Transport", "Bills & Utilities",
    "Rent", "Shopping", "Entertainment", "Subscriptions",
    "Health", "Investments", "Education", "Income", "Others"
]

PAYMENT_MODES_LIST = ["UPI", "Card", "Net Banking", "Cash", "Auto-debit"]


def format_inr(number: float) -> str:
    """Format float into Indian Rupee style string ₹1,23,456.00."""
    try:
        s, *d = f"{number:.2f}".split(".")
        extra = f".{d[0]}" if d else ""
        if len(s) <= 3:
            return f"₹{s}{extra}"
        last_three = s[-3:]
        remaining = s[:-3]
        out = ""
        while len(remaining) > 2:
            out = f",{remaining[-2:]}{out}"
            remaining = remaining[:-2]
        if remaining:
            out = f"{remaining}{out}"
        return f"₹{out},{last_three}{extra}"
    except Exception:
        return f"₹{number:,.2f}"


async def run_anomaly_detection(db: AsyncSession, user_id: int) -> Tuple[int, int, List[Transaction]]:
    """
    Executes Scikit-Learn Isolation Forest on user's transactions using:
    1. Transaction amount & log amount
    2. Category-relative expenditure (z-score)
    3. Spending-frequency features (same-day frequency and inter-transaction interval)
    4. Day of week (0=Mon to 6=Sun)
    5. Payment mode encoded feature

    Strict rules:
    - Never use the word 'fraud'; only 'suspicious' or 'unusual'.
    - Fits automatically when a user has at least 30 transactions.
    - All reasons formatted in ₹.
    """
    # 1. Fetch user expense transactions
    stmt = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
        .order_by(Transaction.transaction_date.asc())
    )
    result = await db.execute(stmt)
    tx_list: List[Transaction] = list(result.scalars().all())

    if not tx_list:
        update_model_status(user_id, "isolation_forest", "not_enough_data", records_used=0, message="0/30 transactions")
        return 0, 0, []

    total_evaluated = len(tx_list)

    if total_evaluated < 30:
        update_model_status(
            user_id,
            "isolation_forest",
            "not_enough_data",
            records_used=total_evaluated,
            message=f"{total_evaluated}/30 transactions needed for Isolation Forest",
        )
        # Statistical baseline fallback
        flagged = []
        amounts = [float(t.amount) for t in tx_list]
        avg_amt = float(np.mean(amounts))
        std_amt = float(np.std(amounts)) or 1.0

        for tx in tx_list:
            amt = float(tx.amount)
            if amt > avg_amt + 3.0 * std_amt and amt > 5000:
                tx.is_anomaly = True
                tx.anomaly_score = 0.85
                tx.anomaly_reason = f"Unusually large expenditure of {format_inr(amt)} significantly above average ({format_inr(avg_amt)})"
                tx.anomaly_detected_at = datetime.utcnow()
                flagged.append(tx)
        if flagged:
            await db.commit()
        return total_evaluated, len(flagged), flagged

    # Full Isolation Forest on >= 30 transactions
    update_model_status(user_id, "isolation_forest", "training", records_used=total_evaluated)

    data = []
    for tx in tx_list:
        tx_d = tx.transaction_date.date() if isinstance(tx.transaction_date, datetime) else tx.transaction_date
        data.append({
            "id": tx.id,
            "amount": float(tx.amount),
            "category": str(tx.category),
            "payment_mode": getattr(tx, "payment_mode", "UPI") or "UPI",
            "date": tx_d,
            "day_of_week": tx_d.weekday(),
            "obj": tx,
        })
    df = pd.DataFrame(data)

    # Feature 1: Log amount
    df["log_amount"] = np.log1p(df["amount"])

    # Feature 2: Category z-score
    cat_means = df.groupby("category")["amount"].transform("mean")
    cat_stds = df.groupby("category")["amount"].transform("std").fillna(1.0)
    df["cat_zscore"] = (df["amount"] - cat_means) / (cat_stds + 1e-5)
    df["cat_mean"] = cat_means

    # Feature 3: Spending frequency (same-day count)
    df["same_day_freq"] = df.groupby("date")["amount"].transform("count")

    # Feature 4: Day of week
    df["dow"] = df["day_of_week"]

    # Feature 5: Payment mode encoding (numerical map)
    mode_map = {m: idx for idx, m in enumerate(PAYMENT_MODES_LIST)}
    df["mode_code"] = df["payment_mode"].map(lambda x: mode_map.get(x, 0))

    # Numerical feature matrix: amount, category, frequency, day of week, payment mode
    feature_cols = ["log_amount", "cat_zscore", "same_day_freq", "dow", "mode_code"]
    X = df[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit Isolation Forest (contamination 3-6%)
    contamination_rate = min(0.06, max(0.02, 5.0 / total_evaluated))
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=contamination_rate,
        random_state=42,
    )
    predictions = iso_forest.fit_predict(X_scaled)
    decision_scores = iso_forest.decision_function(X_scaled)

    min_score, max_score = decision_scores.min(), decision_scores.max()
    score_range = max(1e-5, max_score - min_score)
    normalized_scores = 1.0 - ((decision_scores - min_score) / score_range)

    flagged_txs: List[Transaction] = []
    now = datetime.utcnow()

    for idx, (pred, norm_score) in enumerate(zip(predictions, normalized_scores)):
        tx = df.iloc[idx]["obj"]
        amt = float(df.iloc[idx]["amount"])
        cat = str(df.iloc[idx]["category"])
        cat_mean = float(df.iloc[idx]["cat_mean"])
        freq = int(df.iloc[idx]["same_day_freq"])
        mode = str(df.iloc[idx]["payment_mode"])

        # Preserve previously authored or detected anomaly reason if already set
        if tx.is_anomaly and tx.anomaly_reason and "₹" in tx.anomaly_reason:
            flagged_txs.append(tx)
            continue

        if pred == -1:  # Outlier flagged by Isolation Forest
            tx.is_anomaly = True
            tx.anomaly_score = round(float(norm_score), 4)
            tx.anomaly_detected_at = now

            # Synthesize plain language reason with rupee amounts
            amt_str = format_inr(amt)
            mean_str = format_inr(cat_mean)

            if amt > 2.5 * cat_mean and amt > 2000:
                reason = f"{amt_str} is far above your usual {cat} spend of about {mean_str}"
            elif freq >= 4:
                reason = f"Unusual spending frequency ({freq} transactions recorded in a single day)"
            elif amt > 15000:
                reason = f"High-value unusual transaction of {amt_str} via {mode} flagged for review"
            else:
                reason = f"Suspicious transaction pattern deviating from normal {cat} spending habits"

            tx.anomaly_reason = reason
            flagged_txs.append(tx)

    await db.commit()
    for tx in flagged_txs:
        await db.refresh(tx)

    update_model_status(
        user_id,
        "isolation_forest",
        "ready",
        records_used=total_evaluated,
        message=f"Isolation Forest active ({len(flagged_txs)} unusual transaction(s) flagged)",
    )

    return total_evaluated, len(flagged_txs), flagged_txs
