from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.app.main import app
from backend.app.core.config import settings


def test_live_core_flow():
    email = f"smoke-{uuid4().hex}@example.invalid"
    client = TestClient(app)
    user_id = None
    try:
        registered = client.post("/api/auth/register", json={"full_name": "Smoke Test", "email": email, "password": "test-password-123"})
        assert registered.status_code == 201, registered.text
        user_id = registered.json()["id"]
        login = client.post("/api/auth/login", data={"username": email, "password": "test-password-123"})
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        created = client.post("/api/transactions", json={"amount": 1000, "transaction_type": "income", "category": "Salary", "merchant": "Employer", "transaction_date": "2026-10-01"}, headers=headers)
        assert created.status_code == 201, created.text
        transaction_id = created.json()["id"]
        edited = client.put(f"/api/transactions/{transaction_id}", json={"amount": 1200}, headers=headers)
        assert edited.status_code == 200 and edited.json()["amount"] == 1200
        listed = client.get("/api/transactions", params={"search": "Employer", "transaction_type": "income"}, headers=headers)
        assert listed.status_code == 200 and len(listed.json()) == 1
        budget = client.post("/api/budgets", json={"category": "Food", "limit_amount": 250, "month": "2026-10"}, headers=headers)
        assert budget.status_code == 201, budget.text
        imported = client.post("/api/transactions/import", files={"file": ("sample.csv", b"amount,transaction_type,category,merchant,description,transaction_date\n25.50,expense,Food,Market,Lunch,2026-10-02\n", "text/csv")}, headers=headers)
        assert imported.status_code == 201 and imported.json()["imported"] == 1, imported.text
        summary = client.get("/api/dashboard/summary", headers=headers)
        assert summary.status_code == 200 and summary.json()["total_income"] == 1200
        assert client.delete(f"/api/transactions/{transaction_id}", headers=headers).status_code == 204
    finally:
        if user_id is not None:
            engine = create_engine(settings.DATABASE_URL)
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM transactions WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM budgets WHERE user_id = :user_id"), {"user_id": user_id})
                connection.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            engine.dispose()
