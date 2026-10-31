# backend/tests/test_india_flow.py
import sys
import os
import io
import time
import random
import string
import requests
from PIL import Image, ImageDraw

BASE = "http://127.0.0.1:8000/api"

def random_email(prefix="user"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}@finpulse.in"

def run_tests():
    print("=" * 70)
    print("FINPULSE AI - INDIA DAILY EXPENSE MANAGER E2E VERIFICATION SUITE")
    print("=" * 70)

    # 1. Register User A
    email_a = random_email("rahul")
    password = "Password123!"
    print(f"\n[1] Registering User A ({email_a})...")
    reg_a = requests.post(f"{BASE}/auth/register", json={
        "full_name": "Rahul Sharma",
        "email": email_a,
        "password": password
    })
    assert reg_a.status_code == 201, f"User A registration failed: {reg_a.text}"
    user_a_id = reg_a.json()["id"]
    print(f"  -> User A registered with ID {user_a_id}")

    # Login User A
    login_a = requests.post(f"{BASE}/auth/login", data={"username": email_a, "password": password})
    assert login_a.status_code == 200, f"User A login failed: {login_a.text}"
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print("  -> Logged in successfully, token acquired")

    # Verify Bank data pre-connected automatically for User A
    print("\n[2] Verifying pre-connected bank data for User A...")
    txs_res_a = requests.get(f"{BASE}/transactions?limit=300", headers=headers_a)
    assert txs_res_a.status_code == 200, f"Failed to list transactions: {txs_res_a.text}"
    txs_a = txs_res_a.json()
    print(f"  -> User A automatic bank transactions count: {len(txs_a)}")
    assert len(txs_a) >= 120, f"Expected at least 120 bank transactions, got {len(txs_a)}"
    
    first_tx = txs_a[0]
    last_tx = txs_a[-1]
    print(f"  -> Date range: {last_tx['transaction_date'][:10]} to {first_tx['transaction_date'][:10]}")
    print(f"  -> Sample transaction: {first_tx['merchant']} | ₹{first_tx['amount']} | Category: {first_tx['category']} | Mode: {first_tx['payment_mode']} | Source: {first_tx['source']}")
    assert first_tx["payment_mode"] in ["UPI", "Card", "Net Banking", "Cash", "Auto-debit"]
    assert first_tx["currency"] == "INR"

    # 2. Register User B and verify distinct persona data
    email_b = random_email("priya")
    print(f"\n[3] Registering User B ({email_b}) to verify data variance...")
    reg_b = requests.post(f"{BASE}/auth/register", json={
        "full_name": "Priya Patel",
        "email": email_b,
        "password": password
    })
    assert reg_b.status_code == 201
    user_b_id = reg_b.json()["id"]

    login_b = requests.post(f"{BASE}/auth/login", data={"username": email_b, "password": password})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    txs_res_b = requests.get(f"{BASE}/transactions?limit=300", headers=headers_b)
    txs_b = txs_res_b.json()
    print(f"  -> User B automatic bank transactions count: {len(txs_b)}")

    # Verify User A and User B have different transaction histories
    dash_a = requests.get(f"{BASE}/dashboard/summary", headers=headers_a).json()
    dash_b = requests.get(f"{BASE}/dashboard/summary", headers=headers_b).json()
    print(f"  -> User A Bank: {dash_a.get('bank_name')} | Balance: ₹{dash_a['total_balance']:,.2f}")
    print(f"  -> User B Bank: {dash_b.get('bank_name')} | Balance: ₹{dash_b['total_balance']:,.2f}")
    assert dash_a["total_balance"] != dash_b["total_balance"], "User A and User B should have different balances!"
    print("  -> CONFIRMED: Data differs per user (seeded by user ID)")

    # 3. Test Dashboard Summary for User A
    print("\n[4] Testing Dashboard Summary...")
    print(f"  -> Total Balance: ₹{dash_a['total_balance']:,.2f}")
    print(f"  -> Monthly Spending: ₹{dash_a['monthly_expenses']:,.2f}")
    print(f"  -> Monthly Savings: ₹{dash_a['monthly_savings']:,.2f}")
    print(f"  -> Today's Spend: ₹{dash_a['today_spend']:,.2f}")
    print(f"  -> Demo Notice: {dash_a['bank_demo_notice']}")
    print(f"  -> Daily Spending Trend points: {len(dash_a['daily_spending_trend'])}")
    print(f"  -> Categories: {', '.join([c['category'] for c in dash_a['expense_by_category'][:4]])}")

    # 4. Test Live Transaction Arrival
    print("\n[5] Testing Live Transaction Feed...")
    sim_res = requests.post(f"{BASE}/plaid/simulate-transaction", headers=headers_a)
    assert sim_res.status_code == 200, f"Simulation failed: {sim_res.text}"
    sim_data = sim_res.json()
    print(f"  -> Live purchase arrived: {sim_data.get('message')}")
    print(f"  -> Source: {sim_data.get('source')} | Mode: {sim_data.get('payment_mode')}")

    # 5. Test Receipt OCR Scanner with Indian bill
    print("\n[6] Testing EasyOCR Receipt Scanner...")
    img = Image.new("RGB", (450, 320), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((25, 20), "EMPIRE RESTAURANT", fill=(0, 0, 0))
    draw.text((25, 50), "Church Street, Bengaluru", fill=(0, 0, 0))
    draw.text((25, 80), "Date: 26/10/2026", fill=(0, 0, 0))
    draw.text((25, 110), "Chicken Biryani x2   Rs. 560.00", fill=(0, 0, 0))
    draw.text((25, 140), "Fresh Lime Soda x2   Rs. 120.00", fill=(0, 0, 0))
    draw.text((25, 170), "CGST 2.5%            Rs. 17.00", fill=(0, 0, 0))
    draw.text((25, 190), "SGST 2.5%            Rs. 17.00", fill=(0, 0, 0))
    draw.text((25, 225), "Grand Total: Rs. 714.00", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    ocr_res = requests.post(
        f"{BASE}/ocr/scan",
        headers=headers_a,
        files={"file": ("empire_bill.png", buf.getvalue(), "image/png")}
    )
    assert ocr_res.status_code == 200, f"OCR scan failed: {ocr_res.text}"
    ocr_data = ocr_res.json()
    print(f"  -> OCR Extracted Amount: ₹{ocr_data['amount']}")
    print(f"  -> OCR Extracted Merchant: {ocr_data['merchant']}")
    print(f"  -> OCR Extracted Date: {ocr_data['date']}")
    print(f"  -> OCR Category: {ocr_data['category']}")

    # Save transaction with source "receipt_ocr"
    save_receipt = requests.post(f"{BASE}/transactions", headers=headers_a, json={
        "amount": ocr_data["amount"],
        "currency": "INR",
        "transaction_type": "expense",
        "category": ocr_data["category"],
        "merchant": ocr_data["merchant"],
        "description": "Empire Restaurant Biryani dinner",
        "transaction_date": ocr_data["date"],
        "payment_mode": "UPI",
        "source": "receipt_ocr"
    })
    assert save_receipt.status_code == 201
    print("  -> Saved scanned receipt into ledger with source 'receipt_ocr'")

    # 6. Test Manual Transaction Entry
    print("\n[7] Testing Manual Transaction Entry...")
    man_tx = requests.post(f"{BASE}/transactions", headers=headers_a, json={
        "amount": 160.00,
        "currency": "INR",
        "transaction_type": "expense",
        "category": "Food & Dining",
        "merchant": "Chai Point",
        "description": "Ginger Chai & Samosa",
        "transaction_date": "2026-10-30",
        "payment_mode": "UPI",
        "source": "manual"
    })
    assert man_tx.status_code == 201
    print(f"  -> Manual entry saved: ₹{man_tx.json()['amount']} at {man_tx.json()['merchant']} via {man_tx.json()['payment_mode']}")

    # 7. Test Models Status & Forecast & Anomalies
    print("\n[8] Testing Model Training & Status...")
    model_stat = requests.get(f"{BASE}/models/status", headers=headers_a).json()
    print(f"  -> LSTM Status: {model_stat['lstm']['state']} ({model_stat['lstm']['records_used']} records)")
    print(f"  -> Isolation Forest Status: {model_stat['isolation_forest']['state']} ({model_stat['isolation_forest']['records_used']} records)")

    # Test Forecast
    fc = requests.get(f"{BASE}/forecast/?horizon_days=30", headers=headers_a).json()
    print(f"  -> Forecast Model Used: {fc['model_used']}")
    print(f"  -> Projected End Balance: ₹{fc['projected_end_balance']:,.2f}")
    print(f"  -> Shortage Flag: {fc['shortage_flag']}")

    # Test Anomalies
    anom_res = requests.get(f"{BASE}/anomalies/", headers=headers_a).json()
    print(f"  -> Total Anomalies detected: {len(anom_res)}")
    if anom_res:
        first_anom = anom_res[0]
        print(f"  -> First Anomaly: ₹{first_anom['amount']} at {first_anom['merchant']} | Reason: {first_anom['anomaly_reason']}")
        # Mark reviewed
        mark_res = requests.post(f"{BASE}/anomalies/{first_anom['id']}/review", headers=headers_a)
        assert mark_res.status_code == 200, f"Mark reviewed failed: {mark_res.text}"
        print(f"  -> Marked anomaly #{first_anom['id']} as reviewed: {mark_res.json()['is_reviewed']}")

    # 8. Test AI Financial Advisor with the 6 required questions
    print("\n[9] Testing AI Financial Advisor (Daily Expense Coach)...")
    questions = [
        "Where am I spending the most?",
        "How much did I spend this month?",
        "Will I run out of money before month end?",
        "Which expenses can I reduce?",
        "What unusual transactions were detected?",
        "Give me a one-line summary of my week."
    ]

    answers = []
    for q in questions:
        print(f"\n  Q: \"{q}\"")
        chat_res = requests.post(f"{BASE}/assistant/chat", headers=headers_a, json={"message": q})
        assert chat_res.status_code == 200, f"Chat failed for '{q}': {chat_res.text}"
        data = chat_res.json()
        resp = data["response"]
        src = data.get("source", "Unknown")
        print(f"  Source: {src}")
        # Print first 250 characters of response
        clean_resp = resp.replace("\n", " ")[:200]
        print(f"  A: {clean_resp}...")
        # Check that rupee symbol or numbers are present
        assert "₹" in resp or "Rs" in resp or any(char.isdigit() for char in resp), f"Response missing financial amounts: {resp}"
        answers.append(resp)

    # Confirm all 6 answers differ from each other
    unique_answers = set(answers)
    print(f"\n  -> Unique answers count: {len(unique_answers)} / {len(questions)}")
    assert len(unique_answers) == len(questions), "BUG CHECK: Answers must differ for each question!"

    print("\n" + "=" * 70)
    print("ALL 9 TEST STAGES PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
