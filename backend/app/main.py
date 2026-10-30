# backend/app/main.py
import sys
import asyncio

# Psycopg 3 async requires a Selector event loop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .api.routes import router
from .db.session import init_db, AsyncSessionLocal
from .models.plaid_item import PlaidItem
from .services.plaid_service import sync_all_items
from .ml.anomaly_detector import run_anomaly_detection

logger = logging.getLogger("finpulse")


async def _plaid_background_sync_loop():
    logger.info("Plaid background sync scheduled (runs every 120 seconds).")
    while True:
        try:
            await asyncio.sleep(120)
            async with AsyncSessionLocal() as db:
                user_ids_stmt = select(PlaidItem.user_id).where(PlaidItem.status == "active").distinct()
                user_ids = (await db.execute(user_ids_stmt)).scalars().all()
                for uid in user_ids:
                    try:
                        res = await sync_all_items(db, uid)
                        if res.get("synced", 0) > 0:
                            logger.info(f"Background Plaid sync added {res['synced']} txs for user {uid}")
                            await run_anomaly_detection(db, uid)
                    except Exception as err:
                        logger.error("Background sync user error: %s", type(err).__name__)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Background sync loop error: %s", type(e).__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    sync_task = asyncio.create_task(_plaid_background_sync_loop())
    try:
        yield
    finally:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="FinPulse AI Backend",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS for local dev (frontend runs on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
