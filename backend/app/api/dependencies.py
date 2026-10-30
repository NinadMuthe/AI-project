# backend/app/api/dependencies.py
from fastapi import Depends
from ..db.session import get_db as _get_db

async def get_db():
    async for db in _get_db():
        yield db

