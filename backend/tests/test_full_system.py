import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath("backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


async def run_full_system_verification():
    print("=" * 60)
    print("FINPULSE AI - COMPREHENSIVE END-TO-END TEST SUITE")
    print("=" * 60)

    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Health & Docs
        h = await ac.get("/health")
        assert h.status_code == 200
        d = await ac.get("/docs")
        assert d.status_code == 200
        print("[PASS] Stage 1: Health & API Documentation active")

        # 2. User Registration & Authentication
        user_email = f"demo_eval_{int(time.time())}@finpulse.local"
        reg = await ac.post("/api/auth/register", json={
            "full_name": "Full System Demo User",
            "email": user_email,
            "password": "ValidPassword123!",
        })
        assert reg.status_code == 201

        login = await ac.post("/api/auth/login", data={"username": user_email, "password": "ValidPassword123!"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = await ac.get("/api/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["email"] == user_email
        print(f"[PASS] Stage 1: JWT Authentication & User Isolation verified (User ID: {me.json()['id']})")

        # 3. Stage 5 Baseline check (before demo data)
        fc_sparse = await ac.get("/api/forecast?horizon=30", headers=headers)
        assert fc_sparse.status_code == 200
        assert fc_sparse.json()["is_baseline"] is True
        print("[PASS] Stage 5: Cold-start fallback properly returns BASELINE projection (never pretends LSTM trained)")

        # 4. Stage 3: Demo Data Import & Duplicate Prevention
        imp1 = await ac.post("/api/transactions/import-demo", headers=headers)
        assert imp1.status_code == 201
        res1 = imp1.json()
        assert res1["imported"] > 200
        assert res1["duplicates"] == 0
        print(f"[PASS] Stage 3: Demo Data Import ({res1['imported']} transactions across 6 months)")

        imp2 = await ac.post("/api/transactions/import-demo", headers=headers)
        assert imp2.status_code == 201
        res2 = imp2.json()
        assert res2["imported"] == 0
        assert res2["duplicates"] == res1["imported"]
        print(f"[PASS] Stage 3: Duplicate protection confirmed (0 new, {res2['duplicates']} skipped)")

        # 5. Stage 4: Dashboard Aggregations
        dash = await ac.get("/api/dashboard/summary", headers=headers)
        assert dash.status_code == 200
        d_val = dash.json()
        assert d_val["total_income"] > 0
        assert d_val["total_expenses"] > 0
        assert len(d_val["recent_transactions"]) == 5
        assert len(d_val["expense_by_category"]) > 0
        assert len(d_val["monthly_cash_flow"]) > 0
        print(f"[PASS] Stage 4: Dashboard aggregation from DB (Income: ${d_val['total_income']:.2f}, Expenses: ${d_val['total_expenses']:.2f})")

        # 6. Stage 2: Transaction CRUD & Search
        tx_res = await ac.post("/api/transactions/", json={
            "amount": 99.99,
            "transaction_type": "expense",
            "category": "Shopping",
            "merchant": "Test Mart",
            "description": "E2E verification expense",
            "transaction_date": "2026-10-29",
        }, headers=headers)
        assert tx_res.status_code == 201
        new_tx_id = tx_res.json()["id"]

        search_res = await ac.get("/api/transactions/?search=verification", headers=headers)
        assert search_res.status_code == 200
        assert any(t["id"] == new_tx_id for t in search_res.json())

        del_res = await ac.delete(f"/api/transactions/{new_tx_id}", headers=headers)
        assert del_res.status_code == 204
        print("[PASS] Stage 2: Transaction CRUD, search, and filtering verified")

        # 7. Stage 5: PyTorch LSTM Expense Forecasting
        fc_res = await ac.get("/api/forecast?horizon=30", headers=headers)
        assert fc_res.status_code == 200
        fc_data = fc_res.json()
        assert fc_data["is_baseline"] is False
        assert "PyTorch LSTM" in fc_data["model_used"]
        forecast_pts = [p for p in fc_data["series"] if p["is_forecast"]]
        assert len(forecast_pts) == 30
        print(f"[PASS] Stage 5: PyTorch LSTM neural network forecast trained & predicted {len(forecast_pts)} days (Shortage flag: {fc_data['shortage_flag']})")

        # 8. Stage 6: Isolation Forest Anomaly Detection
        anom_run = await ac.post("/api/anomalies/detect", headers=headers)
        assert anom_run.status_code == 200
        anom_res = anom_run.json()
        assert anom_res["anomalies_flagged"] > 0

        for a in anom_res["anomalies"]:
            r = a["anomaly_reason"].lower()
            assert "fraud" not in r, f"Forbidden term 'fraud' found: {r}"
            assert ("unusual" in r or "suspicious" in r), f"Required phrasing missing: {r}"

        anom_id = anom_res["anomalies"][0]["id"]
        rev_res = await ac.post(f"/api/anomalies/{anom_id}/review", headers=headers)
        assert rev_res.status_code == 200
        assert rev_res.json()["is_reviewed"] is True
        print(f"[PASS] Stage 6: Isolation Forest flagged {anom_res['anomalies_flagged']} unusual expenses; 'mark as reviewed' flow verified")

        print("=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY! FINPULSE AI READY FOR DEMO.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_full_system_verification())
