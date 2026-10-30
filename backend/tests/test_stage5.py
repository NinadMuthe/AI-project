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
        # Case 1: Insufficient data user
        user1_email = f"sparse_user_{int(time.time())}@finpulse.local"
        await ac.post("/api/auth/register", json={
            "full_name": "Sparse User",
            "email": user1_email,
            "password": "Password123!",
        })
        login1 = await ac.post("/api/auth/login", data={"username": user1_email, "password": "Password123!"})
        headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}

        # Add only 2 transactions
        await ac.post("/api/transactions/", json={
            "amount": 50.0,
            "transaction_type": "expense",
            "category": "Food",
            "merchant": "Corner Cafe",
            "description": "Lunch",
            "transaction_date": "2026-10-25",
        }, headers=headers1)

        r_base = await ac.get("/api/forecast?horizon=30", headers=headers1)
        assert r_base.status_code == 200, f"Sparse forecast failed: {r_base.text}"
        data_base = r_base.json()
        print("Test 1 (Sparse Data):")
        print(f"  Model used:  {data_base['model_used']}")
        print(f"  Is Baseline: {data_base['is_baseline']}")
        print(f"  Message:     {data_base['message']}")
        assert data_base["is_baseline"] is True
        assert "BASELINE" in data_base["model_used"]
        print("PASS: Fallback to clearly labelled BASELINE verified when data is insufficient")

        # Case 2: User with full 6 months demo data
        user2_email = f"lstm_user_{int(time.time())}@finpulse.local"
        await ac.post("/api/auth/register", json={
            "full_name": "LSTM User",
            "email": user2_email,
            "password": "Password123!",
        })
        login2 = await ac.post("/api/auth/login", data={"username": user2_email, "password": "Password123!"})
        headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

        # Import 6-month demo data
        await ac.post("/api/transactions/import-demo", headers=headers2)

        # Call forecast endpoint
        r_lstm = await ac.get("/api/forecast?horizon=30", headers=headers2)
        assert r_lstm.status_code == 200, f"LSTM forecast failed: {r_lstm.text}"
        data_lstm = r_lstm.json()
        print("\nTest 2 (Sufficient Data with PyTorch LSTM):")
        print(f"  Model used:          {data_lstm['model_used']}")
        print(f"  Is Baseline:         {data_lstm['is_baseline']}")
        print(f"  Current Balance:     ${data_lstm['current_balance']:.2f}")
        print(f"  Projected End Bal:   ${data_lstm['projected_end_balance']:.2f}")
        print(f"  Shortage Flag:       {data_lstm['shortage_flag']}")
        if data_lstm["shortage_flag"]:
            print(f"  Shortage Date:       {data_lstm['shortage_date']}")
            print(f"  Shortage Amount:     ${data_lstm['shortage_amount']:.2f}")
            print(f"  Warning:             {data_lstm['shortage_warning']}")
        print(f"  Series Points Count: {len(data_lstm['series'])}")

        assert data_lstm["is_baseline"] is False
        assert "PyTorch LSTM" in data_lstm["model_used"]
        assert len(data_lstm["series"]) > 30
        predicted_points = [p for p in data_lstm["series"] if p["is_forecast"]]
        assert len(predicted_points) == 30
        assert all(p["predicted_expense"] is not None for p in predicted_points)
        print("PASS: Real PyTorch LSTM forecasting and balance projection verified")


if __name__ == "__main__":
    asyncio.run(main())
