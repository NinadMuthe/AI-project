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
        email = f"demo_tester_{int(time.time())}@finpulse.local"
        await ac.post("/api/auth/register", json={
            "full_name": "Demo Tester",
            "email": email,
            "password": "DemoPassword123!",
        })
        login_res = await ac.post("/api/auth/login", data={"username": email, "password": "DemoPassword123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # First import
        r = await ac.post("/api/transactions/import-demo", headers=headers)
        assert r.status_code == 201, f"Import demo failed: {r.text}"
        data = r.json()
        print(f"PASS: Demo import ({data['imported']} imported, {data['duplicates']} duplicates)")
        assert data["imported"] > 200, f"Expected >200 demo transactions, got {data['imported']}"
        assert data["duplicates"] == 0, f"Expected 0 duplicates on initial import, got {data['duplicates']}"

        # Second import (duplicate prevention)
        r2 = await ac.post("/api/transactions/import-demo", headers=headers)
        assert r2.status_code == 201
        data2 = r2.json()
        print(f"PASS: Duplicate prevention on second import ({data2['imported']} imported, {data2['duplicates']} duplicates)")
        assert data2["imported"] == 0, f"Expected 0 new imported, got {data2['imported']}"
        assert data2["duplicates"] == data["imported"], f"Expected all to be detected as duplicates"


if __name__ == "__main__":
    asyncio.run(main())
