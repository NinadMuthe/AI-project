# backend/app/models/budget.py
from sqlalchemy import CheckConstraint, Column, Integer, String, Numeric, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from ..db.base import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String, nullable=False)
    limit_amount = Column(Numeric(12, 2), nullable=False)
    month = Column(String(7), nullable=False)
    # Retained for compatibility with the original schema; new code uses month.
    period = Column(String, nullable=True)
    created_at = Column(DateTime, server_default="now()")

    owner = relationship("User", back_populates="budgets")

    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="ck_budgets_limit_positive"),
        UniqueConstraint("user_id", "category", "month", name="uq_budget_user_category_month"),
    )
