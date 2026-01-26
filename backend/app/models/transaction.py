from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    symbol = Column(String, index=True)  # Stock symbol (null for DEPOSIT/WITHDRAWAL)
    quantity = Column(Numeric(15, 4))  # Number of shares
    price = Column(Numeric(15, 2))  # Price per share
    total_amount = Column(Numeric(15, 2), nullable=False)  # Total transaction amount
    fees = Column(Numeric(15, 2), default=0.00)
    notes = Column(String)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
