import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


async def main():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"dashboard_tester_{int(time.time())}@finpulse.local"
        await ac.post("/api/auth/register", json={
            "full_name": "Dashboard Tester",
            "email": email,
            "password": "Password123!",
        })
        login_res = await ac.post("/api/auth/login", data={"username": email, "password": "Password123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Import demo data first
        import_res = await ac.post("/api/transactions/import-demo", headers=headers)
        assert import_res.status_code == 201
        print(f"PASS: Imported demo data ({import_res.json()['imported']} transactions)")

        # Fetch dashboard summary
        r = await ac.get("/api/dashboard/summary", headers=headers)
        assert r.status_code == 200, f"Dashboard summary failed: {r.text}"
        data = r.json()

        print(f"Dashboard Stats:")
        print(f"  Total Balance:  ${data['total_balance']:.2f}")
        print(f"  Total Income:   ${data['total_income']:.2f}")
        print(f"  Total Expenses: ${data['total_expenses']:.2f}")
        print(f"  Monthly Savings: ${data['monthly_savings']:.2f}")
        print(f"  Recent Txs Count: {len(data['recent_transactions'])}")
        print(f"  Expense Categories: {len(data['expense_by_category'])}")
        print(f"  Monthly Cash Flow entries: {len(data['monthly_cash_flow'])}")

        assert data["total_income"] > 0
        assert data["total_expenses"] > 0
        assert len(data["recent_transactions"]) == 5
        assert len(data["expense_by_category"]) > 0
        assert len(data["monthly_cash_flow"]) > 0
        print("PASS: Dashboard API contract and database values verified")


if __name__ == "__main__":
    asyncio.run(main())
