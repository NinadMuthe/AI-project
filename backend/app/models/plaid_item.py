# backend/app/models/plaid_item.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..db.base import Base


class PlaidItem(Base):
    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String, nullable=False, unique=True)
    # access_token is stored server-side ONLY; NEVER returned to frontend or logged
    access_token = Column(String, nullable=False)
    institution_name = Column(String, nullable=True)
    sync_cursor = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | error

    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="plaid_items")

