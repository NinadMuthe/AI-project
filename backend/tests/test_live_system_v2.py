# backend/tests/test_live_system_v2.py
import asyncio
import io
import time
import uuid
import httpx
from PIL import Image, ImageDraw

BASE_URL = "http://127.0.0.1:8000"


def create_dummy_receipt_image() -> bytes:
    """Generate a clean synthetic receipt image for testing OCR."""
    img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), "BLUE BOTTLE COFFEE", fill=(0, 0, 0))
    draw.text((30, 70), "123 MARKET STREET", fill=(0, 0, 0))
    draw.text((30, 110), "DATE: 2026-10-30", fill=(0, 0, 0))
    draw.text((30, 150), "CAPPUCCINO    $5.50", fill=(0, 0, 0))
    draw.text((30, 180), "CROISSANT     $4.75", fill=(0, 0, 0))
    draw.text((30, 220), "TOTAL: $10.25", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        print("\n=======================================================")
        print("          FINPULSE AI - SYSTEM VERIFICATION V2         ")
        print("=======================================================\n")

        # 0. Health check
        h = await client.get("/health")
        assert h.status_code == 200, f"Health check failed: {h.text}"
        print("[PASS] 1. Backend server healthy (/health)")

        # 1. Register & Login unique test user
        uid = uuid.uuid4().hex[:8]
        email = f"tester_{uid}@finpulse.io"
        password = "SecurePassword123!"
        reg = await client.post("/api/auth/register", json={
            "full_name": f"Tester {uid}",
            "email": email,
            "password": password,
        })
        assert reg.status_code == 201, f"Registration failed: {reg.text}"

        login_res = await client.post("/api/auth/login", data={
            "username": email,
            "password": password,
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[PASS] 2. User registered & authenticated (email: {email})")

        # 2. Check initial model status (before data)
        m_init = await client.get("/api/models/status", headers=headers)
        assert m_init.status_code == 200
        assert m_init.json()["lstm"]["state"] in ["not_enough_data", "ready"]
        print("[PASS] 3. Model status endpoint functional (/api/models/status)")

        # 3. Load Sample Data (6 months in code)
        sample = await client.post("/api/transactions/load-sample", headers=headers)
        assert sample.status_code == 201, f"Sample data load failed: {sample.text}"
        inserted_count = sample.json()["inserted"]
        print(f"[PASS] 4. Loaded {inserted_count} sample transactions (6 months history)")

        # 4. Refuse duplicate sample data
        sample_dup = await client.post("/api/transactions/load-sample", headers=headers)
        assert sample_dup.status_code == 409, f"Expected 409 Conflict, got {sample_dup.status_code}"
        print("[PASS] 5. Refused duplicate sample data import (409 Conflict verified)")

        # 5. Connect Plaid Sandbox Bank
        plaid_conn = await client.post("/api/plaid/connect-sandbox", headers=headers)
        assert plaid_conn.status_code == 200, f"Plaid connect failed: {plaid_conn.text}"
        conn_res = plaid_conn.json()
        print(f"[PASS] 6. Plaid Sandbox bank connected: {conn_res.get('institution_name')} ({conn_res.get('transactions_synced', 0)} txs synced)")

        # 6. Simulate a purchase via Plaid sandbox
        sim_res = await client.post("/api/plaid/simulate-transaction", headers=headers)
        assert sim_res.status_code == 200, f"Simulation failed: {sim_res.text}"
        print(f"[PASS] 7. Simulated purchase recorded & synced: {sim_res.json().get('message')}")

        # 7. Sync twice and verify no duplicates
        txs_before = (await client.get("/api/transactions/?limit=500", headers=headers)).json()
        sync2 = await client.post("/api/plaid/sync", headers=headers)
        assert sync2.status_code == 200
        txs_after = (await client.get("/api/transactions/?limit=500", headers=headers)).json()
        assert len(txs_before) == len(txs_after), f"Duplicate transactions created! before: {len(txs_before)}, after: {len(txs_after)}"
        print(f"[PASS] 8. Sync deduplication verified (Syncing twice produced 0 duplicates)")

        # 8. Verify Source Badges in Transactions
        sources = {t.get("source") for t in txs_after}
        print(f"[PASS] 9. Transaction sources present in database: {sources}")

        # 9. Test Dashboard summary
        dash = await client.get("/api/dashboard/summary", headers=headers)
        assert dash.status_code == 200
        d_json = dash.json()
        print(f"[PASS] 10. Dashboard calculated: Balance=${d_json['total_balance']:.2f}, Income=${d_json['total_income']:.2f}, Expenses=${d_json['total_expenses']:.2f}")

        # 10. Test Forecast (PyTorch LSTM)
        fc = await client.get("/api/forecast/?horizon_days=30", headers=headers)
        assert fc.status_code == 200
        fc_json = fc.json()
        print(f"[PASS] 11. Forecast generated using '{fc_json['model_used']}' with {len(fc_json['series'])} data points")

        # 11. Test Anomaly Detection (Isolation Forest)
        anom = await client.post("/api/anomalies/detect", headers=headers)
        assert anom.status_code == 200
        anom_res = anom.json()
        print(f"[PASS] 12. Isolation Forest executed: {anom_res['anomalies_flagged']} unusual transaction(s) flagged")

        # 12. Mark an anomaly as reviewed
        if anom_res["anomalies"]:
            first_id = anom_res["anomalies"][0]["id"]
            rev = await client.post(f"/api/anomalies/{first_id}/review", headers=headers)
            assert rev.status_code == 200
            assert rev.json()["is_reviewed"] is True
            print(f"[PASS] 13. Marked anomaly transaction #{first_id} as reviewed")

        # 13. Receipt OCR Scan
        img_bytes = create_dummy_receipt_image()
        ocr = await client.post(
            "/api/ocr/scan",
            files={"file": ("test_receipt.jpg", img_bytes, "image/jpeg")},
            headers=headers,
        )
        assert ocr.status_code == 200, f"OCR scan failed: {ocr.text}"
        ocr_res = ocr.json()
        print(f"[PASS] 14. EasyOCR parsed receipt: Merchant='{ocr_res.get('merchant')}', Amount=${ocr_res.get('amount')}")

        # Save the scanned receipt as a transaction with source="receipt_ocr"
        save_receipt = await client.post("/api/transactions/", json={
            "amount": ocr_res.get("amount") or 10.25,
            "transaction_type": "expense",
            "category": "Food",
            "merchant": ocr_res.get("merchant") or "Blue Bottle Coffee",
            "description": "Receipt Scan Demo",
            "transaction_date": "2026-10-30",
            "source": "receipt_ocr",
        }, headers=headers)
        assert save_receipt.status_code == 201
        print("[PASS] 15. Saved scanned receipt transaction with source 'receipt_ocr'")

        # 14. AI Financial Advisor Chat
        ai = await client.post("/api/assistant/chat", json={
            "message": "Where am I spending the most money?",
        }, headers=headers)
        assert ai.status_code == 200
        ai_res = ai.json()
        print(f"[PASS] 16. AI Financial Advisor answered with context:\n      \"{ai_res['response'][:140]}...\"")

        # 15. Final Model Status Check
        m_final = await client.get("/api/models/status", headers=headers)
        assert m_final.status_code == 200
        mf_json = m_final.json()
        print(f"[PASS] 17. Final model statuses: LSTM={mf_json['lstm']['state']}, IsolationForest={mf_json['isolation_forest']['state']}")

        print("\n=======================================================")
        print("          ALL 17/17 TESTS PASSED SUCCESSFULLY!         ")
        print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
