# backend/app/services/plaid_service.py
"""
Plaid sandbox integration.
IMPORTANT: access_token is NEVER returned to the frontend, logged, or stored in plaintext logs.
"""
import logging
import random
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import plaid
from plaid.api import plaid_api
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.sandbox_public_token_create_request_options import SandboxPublicTokenCreateRequestOptions
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.sandbox_transactions_create_request import SandboxTransactionsCreateRequest
from plaid.model.custom_sandbox_transaction import CustomSandboxTransaction
from plaid.model.products import Products

from ..core.config import settings
from ..models.plaid_item import PlaidItem
from ..models.transaction import Transaction

logger = logging.getLogger(__name__)

# Plaid environment mapping
_ENV_MAP = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}

PLAID_CATEGORY_MAP = {
    "FOOD_AND_DRINK": "Food",
    "TRANSPORTATION": "Transport",
    "SHOPS": "Shopping",
    "RECREATION": "Entertainment",
    "ENTERTAINMENT_AND_RECREATION": "Entertainment",
    "ENTERTAINMENT": "Entertainment",
    "UTILITIES": "Bills",
    "BILLS": "Bills",
    "SUBSCRIPTION": "Subscriptions",
    "INCOME": "Income",
    "TRANSFER_IN": "Income",
}


def _get_plaid_client() -> plaid_api.PlaidApi:
    env = _ENV_MAP.get(settings.PLAID_ENV.lower(), plaid.Environment.Sandbox)
    configuration = plaid.Configuration(
        host=env,
        api_key={
            "clientId": settings.PLAID_CLIENT_ID,
            "secret": settings.PLAID_SECRET.get_secret_value(),
        },
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def _map_category(plaid_categories: Optional[list]) -> str:
    if not plaid_categories:
        return "Other"
    for cat in plaid_categories:
        upper = cat.upper().replace(" ", "_").replace("&", "AND")
        for key, val in PLAID_CATEGORY_MAP.items():
            if key in upper:
                return val
    return "Other"


async def connect_sandbox(db: AsyncSession, user_id: int) -> dict:
    """Create sandbox item, exchange token, run first sync. Returns status info (never the token)."""
    client = _get_plaid_client()

    # Check if already connected
    existing = (await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user_id, PlaidItem.status == "active")
    )).scalars().first()
    if existing:
        return {
            "connected": True,
            "institution_name": existing.institution_name,
            "last_synced_at": existing.last_synced_at.isoformat() if existing.last_synced_at else None,
            "message": "Already connected. Use /plaid/sync to refresh.",
        }

    # Create sandbox public token
    pt_request = SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",
        initial_products=[Products("transactions")],
        options=SandboxPublicTokenCreateRequestOptions(
            override_username="user_transactions_dynamic",
            override_password="user_good",
        ),
    )
    pt_response = client.sandbox_public_token_create(pt_request)
    public_token = pt_response["public_token"]

    # Exchange for access token (stored server-side only)
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response["access_token"]  # NEVER log or return this
    item_id = exchange_response["item_id"]

    # Save PlaidItem (access_token stored securely in DB, never returned)
    item = PlaidItem(
        user_id=user_id,
        item_id=item_id,
        access_token=access_token,
        institution_name="First Platypus Bank (Sandbox)",
        status="active",
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Run first sync
    synced = await _sync_item(db, item, client)

    return {
        "connected": True,
        "institution_name": item.institution_name,
        "last_synced_at": item.last_synced_at.isoformat() if item.last_synced_at else None,
        "transactions_synced": synced,
        "message": f"Sandbox bank connected. {synced} transactions imported.",
    }


async def sync_all_items(db: AsyncSession, user_id: int) -> dict:
    """Sync all active Plaid items for a user."""
    items = (await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user_id, PlaidItem.status == "active")
    )).scalars().all()

    if not items:
        return {"synced": 0, "message": "No connected bank accounts. Connect first."}

    client = _get_plaid_client()
    total_synced = 0
    for item in items:
        total_synced += await _sync_item(db, item, client)

    return {
        "synced": total_synced,
        "items_synced": len(items),
        "message": f"Synced {total_synced} new/updated transactions.",
    }


async def _sync_item(db: AsyncSession, item: PlaidItem, client: plaid_api.PlaidApi) -> int:
    """Use /transactions/sync to get new/modified/removed transactions. Returns count added."""
    cursor = item.sync_cursor
    added_count = 0
    has_more = True

    while has_more:
        sync_request = TransactionsSyncRequest(
            access_token=item.access_token,
            **({"cursor": cursor} if cursor else {}),
        )
        try:
            response = client.transactions_sync(sync_request)
        except Exception as e:
            logger.error("Plaid sync error (not logging token): %s", type(e).__name__)
            item.status = "error"
            await db.commit()
            return added_count

        # Process added transactions
        for pt in response["added"]:
            if pt.get("pending", False):
                continue  # skip pending

            amount_raw = float(pt.get("amount", 0))
            if amount_raw == 0:
                continue

            # Plaid: positive = expense (money leaving), negative = income
            if amount_raw > 0:
                tx_type = "expense"
                tx_amount = Decimal(str(round(amount_raw, 2)))
            else:
                tx_type = "income"
                tx_amount = Decimal(str(round(abs(amount_raw), 2)))

            plaid_tx_id = pt.get("transaction_id", "")
            # Check duplicate
            exists = (await db.execute(
                select(Transaction.id).where(Transaction.plaid_transaction_id == plaid_tx_id)
            )).scalar_one_or_none()
            if exists is not None:
                continue

            categories = pt.get("category", []) or []
            category = _map_category(categories)
            merchant = pt.get("merchant_name") or pt.get("name") or "Unknown"
            tx_date_raw = pt.get("date")
            if hasattr(tx_date_raw, "isoformat"):
                tx_date = datetime.combine(tx_date_raw, datetime.min.time())
            else:
                tx_date = datetime.strptime(str(tx_date_raw), "%Y-%m-%d")

            new_tx = Transaction(
                user_id=item.user_id,
                amount=tx_amount,
                transaction_type=tx_type,
                category=category,
                merchant=merchant,
                description=pt.get("name"),
                transaction_date=tx_date,
                source="plaid_sandbox",
                plaid_transaction_id=plaid_tx_id,
                pending=False,
            )
            db.add(new_tx)
            added_count += 1

        # Process removed
        for removed in response.get("removed", []):
            plaid_tx_id = removed.get("transaction_id", "")
            tx_to_del = (await db.execute(
                select(Transaction).where(Transaction.plaid_transaction_id == plaid_tx_id)
            )).scalars().first()
            if tx_to_del:
                await db.delete(tx_to_del)

        cursor = response.get("next_cursor", cursor)
        has_more = response.get("has_more", False)

    item.sync_cursor = cursor
    item.last_synced_at = datetime.utcnow()
    await db.commit()
    return added_count


SIMULATED_PURCHASES = [
    ("Blue Bottle Cafe", 6.75),
    ("Trader Joe's", 68.40),
    ("Shell Gas Station", 45.20),
    ("Uber Ride", 22.80),
    ("Spotify Premium", 10.99),
    ("Target Store", 84.15),
    ("Electronics Depot", 1499.00),  # occasional unusually large one
]

async def simulate_transaction(db: AsyncSession, user_id: int) -> dict:
    """Call /sandbox/transactions/create to simulate realistic purchase, then sync."""
    items = (await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user_id, PlaidItem.status == "active")
    )).scalars().all()

    if not items:
        return {"error": "No connected bank. Connect first."}

    client = _get_plaid_client()
    item = items[0]

    merchant, amount = random.choice(SIMULATED_PURCHASES)
    today = date.today()

    try:
        custom_tx = CustomSandboxTransaction(
            date_transacted=today,
            date_posted=today,
            amount=amount,
            description=f"{merchant} - Debit Card Purchase",
        )
        create_req = SandboxTransactionsCreateRequest(
            access_token=item.access_token,
            transactions=[custom_tx],
        )
        client.sandbox_transactions_create(create_req)
    except Exception as e:
        logger.error("Sandbox transaction creation error: %s", type(e).__name__)

    # Sync after simulating
    synced = await _sync_item(db, item, client)
    return {
        "simulated": True,
        "merchant": merchant,
        "amount": amount,
        "transactions_synced": synced,
        "message": f"Simulated purchase of ${amount:.2f} at {merchant}. {synced} transaction(s) synced.",
    }


async def get_status(db: AsyncSession, user_id: int) -> dict:
    item = (await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user_id)
    )).scalars().first()

    if not item:
        return {"connected": False, "institution_name": None, "last_synced_at": None, "status": None}

    return {
        "connected": item.status == "active",
        "institution_name": item.institution_name,
        "last_synced_at": item.last_synced_at.isoformat() if item.last_synced_at else None,
        "status": item.status,
    }

