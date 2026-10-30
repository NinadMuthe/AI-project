"""Create a local demo account without touching existing user data."""
import asyncio
from datetime import date

from sqlalchemy import select

from backend.app.core.security import get_password_hash
from backend.app.db.session import AsyncSessionLocal, engine
from backend.app.models.transaction import Transaction, TransactionType
from backend.app.models.user import User
from backend.app.models.budget import Budget

DEMO_EMAIL = "demo@finpulse.local"
DEMO_PASSWORD = "DemoPass123!"

SAMPLE_TRANSACTIONS = [
    (5200, TransactionType.INCOME, "Salary", "Northstar Labs", "October salary", date(2026, 10, 1)),
    (850, TransactionType.EXPENSE, "Housing", "Greenview Apartments", "Rent", date(2026, 10, 2)),
    (92.40, TransactionType.EXPENSE, "Groceries", "Fresh Basket", "Weekly groceries", date(2026, 10, 4)),
    (45, TransactionType.EXPENSE, "Transport", "Metro Transit", "Monthly commute", date(2026, 10, 5)),
    (39.99, TransactionType.EXPENSE, "Utilities", "City Power", "Electricity bill", date(2026, 10, 7)),
    (24.50, TransactionType.EXPENSE, "Dining", "Corner Kitchen", "Lunch with colleagues", date(2026, 10, 9)),
    (18.99, TransactionType.EXPENSE, "Entertainment", "StreamBox", "Monthly subscription", date(2026, 10, 11)),
    (150, TransactionType.INCOME, "Freelance", "Cedar Studio", "Website consultation", date(2026, 10, 14)),
    (64.25, TransactionType.EXPENSE, "Health", "Wellness Pharmacy", "Health essentials", date(2026, 10, 16)),
    (110, TransactionType.EXPENSE, "Shopping", "Everyday Goods", "Home supplies", date(2026, 10, 18)),
]


async def create_demo_profile() -> bool:
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none()
        if existing:
            existing_budget = (await session.execute(select(Budget.id).where(Budget.user_id == existing.id))).scalars().first()
            if existing_budget is None:
                session.add_all([
                    Budget(user_id=existing.id, category="Housing", limit_amount=900, month="2026-10", period="monthly"),
                    Budget(user_id=existing.id, category="Food", limit_amount=300, month="2026-10", period="monthly"),
                    Budget(user_id=existing.id, category="Transport", limit_amount=100, month="2026-10", period="monthly"),
                ])
                await session.commit()
            return False
        demo_user = User(full_name="Alex Morgan", email=DEMO_EMAIL, hashed_password=get_password_hash(DEMO_PASSWORD))
        session.add(demo_user)
        await session.flush()
        session.add_all([
            Transaction(user_id=demo_user.id, amount=amount, transaction_type=transaction_type.value,
                        category=category, merchant=merchant, description=description,
                        transaction_date=transaction_date, source="demo")
            for amount, transaction_type, category, merchant, description, transaction_date in SAMPLE_TRANSACTIONS
        ])
        session.add_all([
            Budget(user_id=demo_user.id, category="Housing", limit_amount=900, month="2026-10", period="monthly"),
            Budget(user_id=demo_user.id, category="Food", limit_amount=300, month="2026-10", period="monthly"),
            Budget(user_id=demo_user.id, category="Transport", limit_amount=100, month="2026-10", period="monthly"),
        ])
        await session.commit()
        return True


if __name__ == "__main__":
    created = asyncio.run(create_demo_profile())
    asyncio.run(engine.dispose())
    print("Demo profile created." if created else "Demo profile already exists; no data was changed.")
