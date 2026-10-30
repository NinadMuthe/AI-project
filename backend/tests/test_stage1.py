import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


async def main():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        print("PASS: Health check (/health)")

        r = await ac.get("/docs")
        assert r.status_code == 200, f"Docs check failed: {r.text}"
        print("PASS: Swagger docs (/docs)")

        test_email = "stage1_test_user@finpulse.local"
        reg_data = {
            "full_name": "Stage 1 Verified User",
            "email": test_email,
            "password": "SecurePassword123!",
        }
        r = await ac.post("/api/auth/register", json=reg_data)
        if r.status_code == 201:
            print("PASS: Registration (/api/auth/register)")
        elif r.status_code == 400 and "already registered" in r.text:
            print("PASS: Registration (/api/auth/register) - User existing handled")
        else:
            raise AssertionError(f"Register unexpected response: {r.status_code} {r.text}")

        login_data = {
            "username": test_email,
            "password": "SecurePassword123!",
        }
        r = await ac.post("/api/auth/login", data=login_data)
        assert r.status_code == 200, f"Login failed: {r.text}"
        token = r.json()["access_token"]
        print("PASS: Login & JWT token issuance (/api/auth/login)")

        r = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, f"Protected /me failed: {r.text}"
        data = r.json()
        assert data["email"] == test_email
        print(f"PASS: Protected route verified (/api/auth/me) User ID: {data['id']}")

        r = await ac.get("/api/auth/me")
        assert r.status_code == 401, f"Unauthorized check failed: {r.status_code}"
        print("PASS: Unauthorized access rejection (401)")


if __name__ == "__main__":
    asyncio.run(main())
