from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StockHolding(Base):
    __tablename__ = "stock_holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Numeric(15, 4), nullable=False)  # Total shares owned
    average_cost = Column(Numeric(15, 2), nullable=False)  # Average cost per share
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="holdings")

    # Composite unique constraint: one holding per symbol per user
    __table_args__ = (
        {"schema": None},
    )
