import asyncio
import io
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


async def main():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register user (unique per run)
        import time
        user_email = f"stage2_tester_{int(time.time())}@finpulse.local"
        reg_data = {
            "full_name": "Stage 2 Tester",
            "email": user_email,
            "password": "Password123!",
        }
        await ac.post("/api/auth/register", json=reg_data)

        # Login
        r = await ac.post("/api/auth/login", data={"username": user_email, "password": "Password123!"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Transaction (Income)
        tx_income = {
            "amount": 5000.0,
            "transaction_type": "income",
            "category": "Salary",
            "merchant": "Acme Corp",
            "description": "Monthly pay",
            "transaction_date": str(date.today()),
            "source": "manual",
        }
        r = await ac.post("/api/transactions/", json=tx_income, headers=headers)
        assert r.status_code == 201, f"Create income failed: {r.text}"
        inc_data = r.json()
        inc_id = inc_data["id"]
        print(f"PASS: Create income transaction (ID: {inc_id})")

        # 2. Create Transaction (Expense)
        tx_expense = {
            "amount": 45.50,
            "transaction_type": "expense",
            "category": "Food",
            "merchant": "Whole Foods",
            "description": "Weekly groceries",
            "transaction_date": str(date.today()),
            "source": "manual",
        }
        r = await ac.post("/api/transactions/", json=tx_expense, headers=headers)
        assert r.status_code == 201, f"Create expense failed: {r.text}"
        exp_data = r.json()
        exp_id = exp_data["id"]
        print(f"PASS: Create expense transaction (ID: {exp_id})")

        # 3. Read Transaction
        r = await ac.get(f"/api/transactions/{exp_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["merchant"] == "Whole Foods"
        print("PASS: Read single transaction")

        # 4. Update Transaction
        update_payload = {"amount": 52.00, "description": "Weekly groceries + snack"}
        r = await ac.put(f"/api/transactions/{exp_id}", json=update_payload, headers=headers)
        assert r.status_code == 200
        assert r.json()["amount"] == 52.00
        print("PASS: Update transaction")

        # 5. List with Search and Filter
        # Filter by category
        r = await ac.get("/api/transactions/?category=Salary", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert all(t["category"] == "Salary" for t in r.json())
        print("PASS: Filter by category")

        # Filter by type
        r = await ac.get("/api/transactions/?transaction_type=expense", headers=headers)
        assert r.status_code == 200
        assert all(t["transaction_type"] == "expense" for t in r.json())
        print("PASS: Filter by type")

        # Search
        r = await ac.get("/api/transactions/?search=groceries", headers=headers)
        assert r.status_code == 200
        assert any("groceries" in (t["description"] or "").lower() for t in r.json())
        print("PASS: Search by keyword")

        # 6. CSV Import
        csv_content = """amount,transaction_type,category,merchant,description,transaction_date
120.00,expense,Utilities,Electric Co,Power bill,2026-10-01
75.25,expense,Food,Supermarket,Dinner ingredients,2026-10-02
3200.00,income,Salary,Acme Corp,Monthly direct deposit,2026-10-01
"""
        files = {"file": ("test_import.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        r = await ac.post("/api/transactions/import", files=files, headers=headers)
        assert r.status_code == 201, f"CSV import failed: {r.text}"
        res = r.json()
        assert res["imported"] >= 1
        print(f"PASS: CSV import ({res['imported']} imported, {res['duplicates']} duplicates)")

        # Test duplicate prevention on second import of same CSV
        files2 = {"file": ("test_import.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        r2 = await ac.post("/api/transactions/import", files=files2, headers=headers)
        assert r2.status_code == 201
        res2 = r2.json()
        assert res2["duplicates"] == 3
        print("PASS: Duplicate detection on duplicate CSV upload")

        # 7. Delete Transaction
        r = await ac.delete(f"/api/transactions/{exp_id}", headers=headers)
        assert r.status_code == 204
        r = await ac.get(f"/api/transactions/{exp_id}", headers=headers)
        assert r.status_code == 404
        print("PASS: Delete transaction")


if __name__ == "__main__":
    asyncio.run(main())
