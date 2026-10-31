# backend/app/models/transaction.py
from sqlalchemy import CheckConstraint, Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Float, func
from sqlalchemy.orm import relationship
from ..db.base import Base
import enum

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class PaymentMode(str, enum.Enum):
    UPI = "UPI"
    CARD = "Card"
    NET_BANKING = "Net Banking"
    CASH = "Cash"
    AUTO_DEBIT = "Auto-debit"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="INR")
    transaction_type = Column(String, nullable=False)  # "income" or "expense"
    category = Column(String, nullable=False)
    merchant = Column(String, nullable=True)
    description = Column(String, nullable=True)
    transaction_date = Column(DateTime, nullable=False)
    payment_mode = Column(String, nullable=False, default="UPI")  # UPI, Card, Net Banking, Cash, Auto-debit
    source = Column(String, nullable=False, default="manual")  # manual | bank | bank_demo_feed | receipt_ocr

    # Bank / Plaid fields
    plaid_transaction_id = Column(String, nullable=True, unique=True)
    pending = Column(Boolean, default=False, nullable=False)

    # Anomaly fields
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
