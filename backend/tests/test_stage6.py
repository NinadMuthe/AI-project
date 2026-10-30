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
        user_email = f"anomaly_user_{int(time.time())}@finpulse.local"
        await ac.post("/api/auth/register", json={
            "full_name": "Anomaly Tester",
            "email": user_email,
            "password": "Password123!",
        })
        login_res = await ac.post("/api/auth/login", data={"username": user_email, "password": "Password123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Import demo data
        await ac.post("/api/transactions/import-demo", headers=headers)

        # 2. Trigger anomaly detection
        r = await ac.post("/api/anomalies/detect", headers=headers)
        assert r.status_code == 200, f"Detection failed: {r.text}"
        res = r.json()
        print(f"PASS: Isolation Forest run ({res['total_evaluated']} evaluated, {res['anomalies_flagged']} flagged)")
        assert res["anomalies_flagged"] > 0, "Expected at least one anomaly to be flagged"

        # 3. Check vocabulary constraints (must use 'suspicious' or 'unusual', NEVER 'fraud')
        for anom in res["anomalies"]:
            reason = anom["anomaly_reason"].lower()
            assert "fraud" not in reason, f"Forbidden word 'fraud' found in: {reason}"
            assert ("unusual" in reason or "suspicious" in reason), f"Reason missing required phrasing: {reason}"
            assert anom["anomaly_score"] is not None
            assert anom["anomaly_detected_at"] is not None
            print(f"  Flagged Tx #{anom['id']}: ${anom['amount']:.2f} ({anom['category']}) -> {anom['anomaly_reason']}")
        print("PASS: Verified terminology rules (uses 'suspicious'/'unusual', never 'fraud')")

        # 4. List anomalies
        r_list = await ac.get("/api/anomalies", headers=headers)
        assert r_list.status_code == 200
        anomalies_list = r_list.json()
        assert len(anomalies_list) == res["anomalies_flagged"]
        target_tx_id = anomalies_list[0]["id"]

        # 5. Mark as reviewed
        r_rev = await ac.post(f"/api/anomalies/{target_tx_id}/review", headers=headers)
        assert r_rev.status_code == 200
        assert r_rev.json()["is_reviewed"] is True
        print(f"PASS: Marked transaction #{target_tx_id} as reviewed")

        # 6. Verify unreviewed filter
        r_unrev = await ac.get("/api/anomalies?include_reviewed=false", headers=headers)
        assert r_unrev.status_code == 200
        unreviewed = r_unrev.json()
        assert all(t["id"] != target_tx_id for t in unreviewed)
        print(f"PASS: Filter unreviewed verified ({len(unreviewed)} unreviewed remaining)")


if __name__ == "__main__":
    asyncio.run(main())
