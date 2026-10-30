# backend/app/db/session.py
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from ..core.config import settings
from .base import Base

# Psycopg's async implementation requires a selector event loop on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ensure Stage 6 anomaly columns exist on public.transactions
        for col_def in [
            "is_anomaly BOOLEAN NOT NULL DEFAULT FALSE",
            "anomaly_score DOUBLE PRECISION",
            "anomaly_reason VARCHAR",
            "anomaly_detected_at TIMESTAMP",
            "is_reviewed BOOLEAN NOT NULL DEFAULT FALSE",
            "plaid_transaction_id VARCHAR",
            "pending BOOLEAN NOT NULL DEFAULT FALSE",
        ]:
            col_name = col_def.split()[0]
            await conn.execute(text(
                f"ALTER TABLE transactions ADD COLUMN IF NOT EXISTS {col_def}"
            ))
        # Unique constraint for plaid_transaction_id (ignore if already exists)
        try:
            await conn.execute(text(
                "ALTER TABLE transactions ADD CONSTRAINT uq_plaid_transaction_id "
                "UNIQUE (plaid_transaction_id)"
            ))
        except Exception:
            pass
        # Drop NOT NULL on merchant/description (safe to retry)
        try:
            await conn.execute(text("ALTER TABLE transactions ALTER COLUMN merchant DROP NOT NULL"))
            await conn.execute(text("ALTER TABLE transactions ALTER COLUMN description DROP NOT NULL"))
        except Exception:
            pass
