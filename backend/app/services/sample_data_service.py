# backend/app/services/sample_data_service.py
"""
Generates ~6 months of realistic synthetic transactions IN CODE (no CSV file needed).
Uses source="sample_data". Refuses to run twice for the same user.
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction
from ..schemas.transaction import TransactionCreate
from .transaction_service import create_transaction


def _rand(lo: float, hi: float) -> Decimal:
    return Decimal(str(round(random.uniform(lo, hi), 2)))


async def has_sample_data(db: AsyncSession, user_id: int) -> bool:
    stmt = select(func.count()).select_from(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.source == "sample_data",
    )
    count = (await db.execute(stmt)).scalar_one()
    return count > 0


async def load_sample_data(db: AsyncSession, user_id: int) -> int:
    """Insert ~6 months of synthetic transactions and return count inserted."""
    random.seed(user_id * 12345)  # deterministic per user

    today = datetime.utcnow().date()
    start = today - timedelta(days=182)

    txs: List[TransactionCreate] = []

    # --- Monthly recurring (salary + rent) ---
    for m in range(6):
        pay_date = start + timedelta(days=m * 30 + 1)
        # Salary
        txs.append(TransactionCreate(
            amount=_rand(5400, 5600),
            transaction_type="income",
            category="Income",
            merchant="Employer Corp",
            description="Monthly salary deposit",
            transaction_date=pay_date.isoformat(),
            source="sample_data",
        ))
        # Rent
        rent_date = pay_date + timedelta(days=1)
        txs.append(TransactionCreate(
            amount=_rand(1600, 1700),
            transaction_type="expense",
            category="Bills",
            merchant="City Apartments",
            description="Monthly rent",
            transaction_date=rent_date.isoformat(),
            source="sample_data",
        ))
        # Electricity
        txs.append(TransactionCreate(
            amount=_rand(80, 130),
            transaction_type="expense",
            category="Bills",
            merchant="Power & Light Co.",
            description="Electricity bill",
            transaction_date=(pay_date + timedelta(days=3)).isoformat(),
            source="sample_data",
        ))
        # Internet
        txs.append(TransactionCreate(
            amount=_rand(55, 75),
            transaction_type="expense",
            category="Subscriptions",
            merchant="FiberNet ISP",
            description="Internet subscription",
            transaction_date=(pay_date + timedelta(days=4)).isoformat(),
            source="sample_data",
        ))
        # Netflix
        txs.append(TransactionCreate(
            amount=Decimal("15.99"),
            transaction_type="expense",
            category="Subscriptions",
            merchant="Netflix",
            description="Streaming subscription",
            transaction_date=(pay_date + timedelta(days=5)).isoformat(),
            source="sample_data",
        ))
        # Spotify
        txs.append(TransactionCreate(
            amount=Decimal("9.99"),
            transaction_type="expense",
            category="Subscriptions",
            merchant="Spotify",
            description="Music subscription",
            transaction_date=(pay_date + timedelta(days=5)).isoformat(),
            source="sample_data",
        ))
        # Gym
        txs.append(TransactionCreate(
            amount=_rand(40, 55),
            transaction_type="expense",
            category="Health",
            merchant="FitLife Gym",
            description="Monthly gym membership",
            transaction_date=(pay_date + timedelta(days=6)).isoformat(),
            source="sample_data",
        ))

    # --- Weekly groceries (every 7 days) ---
    food_merchants = ["Whole Foods", "Trader Joe's", "Kroger", "Safeway", "Aldi"]
    d = start
    while d <= today:
        txs.append(TransactionCreate(
            amount=_rand(60, 140),
            transaction_type="expense",
            category="Food",
            merchant=random.choice(food_merchants),
            description="Weekly groceries",
            transaction_date=d.isoformat(),
            source="sample_data",
        ))
        d += timedelta(days=7)

    # --- Daily coffee (weekdays only, ~70% days) ---
    coffee_merchants = ["Starbucks", "Dunkin", "Blue Bottle Coffee", "Local Cafe"]
    d = start
    while d <= today:
        if d.weekday() < 5 and random.random() < 0.7:
            txs.append(TransactionCreate(
                amount=_rand(4, 8),
                transaction_type="expense",
                category="Food",
                merchant=random.choice(coffee_merchants),
                description="Coffee",
                transaction_date=d.isoformat(),
                source="sample_data",
            ))
        d += timedelta(days=1)

    # --- Lunch (weekdays, ~60% days) ---
    lunch_spots = ["Chipotle", "Subway", "McDonald's", "Panera Bread", "Local Diner"]
    d = start
    while d <= today:
        if d.weekday() < 5 and random.random() < 0.6:
            txs.append(TransactionCreate(
                amount=_rand(10, 20),
                transaction_type="expense",
                category="Food",
                merchant=random.choice(lunch_spots),
                description="Lunch",
                transaction_date=d.isoformat(),
                source="sample_data",
            ))
        d += timedelta(days=1)

    # --- Transport (Uber/gas, ~3x per week) ---
    transport_merchants = ["Uber", "Lyft", "Shell Gas", "BP Gas", "Metro Card"]
    d = start
    while d <= today:
        if random.random() < 0.43:
            txs.append(TransactionCreate(
                amount=_rand(8, 35),
                transaction_type="expense",
                category="Transport",
                merchant=random.choice(transport_merchants),
                description="Transport",
                transaction_date=d.isoformat(),
                source="sample_data",
            ))
        d += timedelta(days=1)

    # --- Entertainment (~2x per week) ---
    ent_merchants = ["AMC Theaters", "Steam", "ESPN+", "Bar & Grill", "Concert Tickets"]
    d = start
    while d <= today:
        if random.random() < 0.28:
            txs.append(TransactionCreate(
                amount=_rand(15, 80),
                transaction_type="expense",
                category="Entertainment",
                merchant=random.choice(ent_merchants),
                description="Entertainment",
                transaction_date=d.isoformat(),
                source="sample_data",
            ))
        d += timedelta(days=1)

    # --- Shopping (~1.5x per week) ---
    shop_merchants = ["Amazon", "Target", "Walmart", "Best Buy", "H&M", "ZARA"]
    d = start
    while d <= today:
        if random.random() < 0.21:
            txs.append(TransactionCreate(
                amount=_rand(20, 150),
                transaction_type="expense",
                category="Shopping",
                merchant=random.choice(shop_merchants),
                description="Shopping",
                transaction_date=d.isoformat(),
                source="sample_data",
            ))
        d += timedelta(days=1)

    # --- Healthcare (~monthly) ---
    for offset in [20, 55, 90, 125, 160]:
        if start + timedelta(days=offset) <= today:
            txs.append(TransactionCreate(
                amount=_rand(30, 180),
                transaction_type="expense",
                category="Health",
                merchant=random.choice(["CVS Pharmacy", "Walgreens", "City Clinic"]),
                description="Healthcare / pharmacy",
                transaction_date=(start + timedelta(days=offset)).isoformat(),
                source="sample_data",
            ))

    # --- CLEARLY UNUSUAL large transactions (for anomaly detection) ---
    unusual = [
        ("Electronics Store", "Gaming laptop purchase", 1849.99, 30),
        ("Luxury Boutique", "Designer handbag", 1250.00, 60),
        ("Travel Agency", "International flight booking", 2100.00, 90),
        ("Casino Resort", "Weekend stay", 980.00, 110),
        ("Medical Center", "Emergency room visit", 1500.00, 145),
    ]
    for merchant, desc, amount, day_offset in unusual:
        d_unusual = start + timedelta(days=day_offset)
        if d_unusual <= today:
            txs.append(TransactionCreate(
                amount=Decimal(str(amount)),
                transaction_type="expense",
                category="Shopping" if "Boutique" in merchant or "Electronic" in merchant else "Health" if "Medical" in merchant else "Entertainment",
                merchant=merchant,
                description=desc,
                transaction_date=d_unusual.isoformat(),
                source="sample_data",
            ))

    # Insert all, skip duplicates gracefully
    inserted = 0
    for tx_in in txs:
        try:
            await create_transaction(db, user_id, tx_in)
            inserted += 1
        except Exception:
            await db.rollback()

    return inserted

