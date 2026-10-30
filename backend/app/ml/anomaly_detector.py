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


async def run_anomaly_detection(db: AsyncSession, user_id: int) -> Tuple[int, int, List[Transaction]]:
    """
    Executes Scikit-Learn Isolation Forest on user's transactions using:
    1. Transaction amount
    2. Category-relative expenditure
    3. Spending-frequency features (same-day frequency and inter-transaction interval)

    Strict rule: Never use the word 'fraud'; only 'suspicious' or 'unusual'.
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
        return 0, 0, []

    total_evaluated = len(tx_list)

    # If very few records (less than 6), Isolation Forest cannot reliably partition
    if total_evaluated < 6:
        # Fallback to simple category-based statistical threshold
        flagged = []
        amounts = [float(t.amount) for t in tx_list]
        avg_amt = float(np.mean(amounts))
        std_amt = float(np.std(amounts)) or 1.0

        for tx in tx_list:
            amt = float(tx.amount)
            if amt > avg_amt + 3 * std_amt:
                tx.is_anomaly = True
                tx.anomaly_score = 0.85
                tx.anomaly_reason = f"Unusual expenditure of ${amt:.2f} significantly above average (${avg_amt:.2f})"
                tx.anomaly_detected_at = datetime.utcnow()
                flagged.append(tx)
        if flagged:
            await db.commit()
        return total_evaluated, len(flagged), flagged

    # 2. Build feature matrix
    data = []
    for tx in tx_list:
        tx_d = tx.transaction_date.date() if isinstance(tx.transaction_date, datetime) else tx.transaction_date
        data.append({
            "id": tx.id,
            "amount": float(tx.amount),
            "category": str(tx.category),
            "date": tx_d,
            "obj": tx,
        })
    df = pd.DataFrame(data)

    # Feature 1: Amount & Log amount
    df["log_amount"] = np.log1p(df["amount"])

    # Feature 2: Category average ratio
    cat_means = df.groupby("category")["amount"].transform("mean")
    cat_stds = df.groupby("category")["amount"].transform("std").fillna(1.0)
    df["cat_zscore"] = (df["amount"] - cat_means) / (cat_stds + 1e-5)
    df["cat_mean"] = cat_means

    # Feature 3: Spending frequency (transactions on same date)
    date_counts = df.groupby("date")["amount"].transform("count")
    df["same_day_freq"] = date_counts

    # Feature 4: Days since last transaction
    df["days_diff"] = df["date"].diff().dt.days.fillna(0).clip(lower=0)

    # Prepare numerical feature matrix
    feature_cols = ["log_amount", "cat_zscore", "same_day_freq", "days_diff"]
    X = df[feature_cols].values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit Isolation Forest
    contamination_rate = min(0.08, max(0.02, 5.0 / total_evaluated))
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=contamination_rate,
        random_state=42,
    )
    predictions = iso_forest.fit_predict(X_scaled)
    # Lower decision scores correspond to more anomalous instances
    decision_scores = iso_forest.decision_function(X_scaled)

    # Convert decision function into normalized anomaly score (0 to 1, higher = more unusual)
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

        if pred == -1:  # Outlier flagged by Isolation Forest
            tx.is_anomaly = True
            tx.anomaly_score = round(float(norm_score), 4)
            tx.anomaly_detected_at = now

            # Synthesize short descriptive reason without ever saying 'fraud'
            if amt > 2.5 * cat_mean and amt > 500:
                reason = f"Unusually large expenditure of ${amt:.2f} in {cat} (typical average: ${cat_mean:.2f})"
            elif freq >= 4:
                reason = f"Suspicious spending velocity ({freq} transactions recorded in a single day)"
            elif amt > 1000:
                reason = f"Unusual high-value expense of ${amt:.2f} identified by Isolation Forest"
            else:
                reason = f"Suspicious transaction pattern deviating from regular spending profile"

            tx.anomaly_reason = reason
            flagged_txs.append(tx)

    await db.commit()
    for tx in flagged_txs:
        await db.refresh(tx)

    return total_evaluated, len(flagged_txs), flagged_txs
