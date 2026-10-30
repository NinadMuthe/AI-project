# backend/app/models/transaction.py
from sqlalchemy import CheckConstraint, Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Float, func
from sqlalchemy.orm import relationship
from ..db.base import Base
import enum

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(String, nullable=False)  # "income" or "expense"
    category = Column(String, nullable=False)
    merchant = Column(String, nullable=True)
    description = Column(String, nullable=True)
    transaction_date = Column(DateTime, nullable=False)
    source = Column(String, nullable=False, default="manual")  # manual|sample_data|plaid_sandbox|receipt_ocr

    # Plaid fields
    plaid_transaction_id = Column(String, nullable=True, unique=True)
    pending = Column(Boolean, default=False, nullable=False)

    # Anomaly fields for Stage 6
    is_anomaly = Column(Boolean, default=False, nullable=False)
    anomaly_score = Column(Float, nullable=True)
    anomaly_reason = Column(String, nullable=True)
    anomaly_detected_at = Column(DateTime, nullable=True)
    is_reviewed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )

    owner = relationship("User", back_populates="transactions")

