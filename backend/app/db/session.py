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
        ]:
            await conn.execute(text(f"ALTER TABLE transactions ADD COLUMN IF NOT EXISTS {col_def}"))
