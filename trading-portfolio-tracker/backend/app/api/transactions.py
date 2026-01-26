from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.database import get_db
from app.models.transaction import Transaction, TransactionType
from app.models.stock_holding import StockHolding
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter()

# Pydantic schemas
class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    total_amount: Decimal
    fees: Optional[Decimal] = Decimal("0.00")
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None

    @validator('symbol')
    def validate_symbol(cls, v, values):
        """Validate that symbol is provided for stock transactions"""
        if values.get('transaction_type') in [TransactionType.BUY, TransactionType.SELL]:
            if not v:
                raise ValueError('Symbol is required for BUY/SELL transactions')
        return v

    @validator('quantity')
    def validate_quantity(cls, v, values):
        """Validate that quantity is provided for stock transactions"""
        if values.get('transaction_type') in [TransactionType.BUY, TransactionType.SELL]:
            if not v or v <= 0:
                raise ValueError('Quantity must be greater than 0 for BUY/SELL transactions')
        return v

    @validator('price')
    def validate_price(cls, v, values):
        """Validate that price is provided for stock transactions"""
        if values.get('transaction_type') in [TransactionType.BUY, TransactionType.SELL]:
            if not v or v <= 0:
                raise ValueError('Price must be greater than 0 for BUY/SELL transactions')
        return v

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    transaction_type: TransactionType
    symbol: Optional[str]
    quantity: Optional[Decimal]
    price: Optional[Decimal]
    total_amount: Decimal
    fees: Decimal
    notes: Optional[str]
    transaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction (BUY/SELL/DEPOSIT/WITHDRAWAL)"""
    # Create transaction
    new_transaction = Transaction(
        user_id=current_user.id,
        transaction_type=transaction_data.transaction_type,
        symbol=transaction_data.symbol.upper() if transaction_data.symbol else None,
        quantity=transaction_data.quantity,
        price=transaction_data.price,
        total_amount=transaction_data.total_amount,
        fees=transaction_data.fees,
        notes=transaction_data.notes,
        transaction_date=transaction_data.transaction_date or datetime.utcnow()
    )

    # Update user based on transaction type
    if transaction_data.transaction_type == TransactionType.BUY:
        # Deduct cash for purchase
        total_cost = transaction_data.total_amount + transaction_data.fees
        if current_user.cash_balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient cash balance"
            )
        current_user.cash_balance -= total_cost

        # Update or create stock holding
        holding = db.query(StockHolding).filter(
            StockHolding.user_id == current_user.id,
            StockHolding.symbol == transaction_data.symbol.upper()
        ).first()

        if holding:
            # Update existing holding (calculate new average cost)
            total_cost_basis = (holding.quantity * holding.average_cost) + transaction_data.total_amount
            holding.quantity += transaction_data.quantity
            holding.average_cost = total_cost_basis / holding.quantity
        else:
            # Create new holding
            new_holding = StockHolding(
                user_id=current_user.id,
                symbol=transaction_data.symbol.upper(),
                quantity=transaction_data.quantity,
                average_cost=transaction_data.price
            )
            db.add(new_holding)

    elif transaction_data.transaction_type == TransactionType.SELL:
        # Check if holding exists and has sufficient quantity
        holding = db.query(StockHolding).filter(
            StockHolding.user_id == current_user.id,
            StockHolding.symbol == transaction_data.symbol.upper()
        ).first()

        if not holding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No holdings found for {transaction_data.symbol}"
            )

        if holding.quantity < transaction_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient shares. You have {holding.quantity}, trying to sell {transaction_data.quantity}"
            )

        # Add cash from sale
        total_proceeds = transaction_data.total_amount - transaction_data.fees
        current_user.cash_balance += total_proceeds

        # Update holding
        holding.quantity -= transaction_data.quantity
        if holding.quantity == 0:
            db.delete(holding)

    elif transaction_data.transaction_type == TransactionType.DEPOSIT:
        # Add cash to user
        current_user.cash_balance += transaction_data.total_amount

    elif transaction_data.transaction_type == TransactionType.WITHDRAWAL:
        # Deduct cash from user
        if current_user.cash_balance < transaction_data.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient cash balance for withdrawal"
            )
        current_user.cash_balance -= transaction_data.total_amount

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions for user"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.transaction_date.desc()).all()

    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific transaction details"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction (will recalculate user holdings)"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Reverse the transaction effects
    if transaction.transaction_type == TransactionType.BUY:
        # Refund cash
        total_cost = transaction.total_amount + transaction.fees
        current_user.cash_balance += total_cost

        # Update holding
        holding = db.query(StockHolding).filter(
            StockHolding.user_id == current_user.id,
            StockHolding.symbol == transaction.symbol
        ).first()

        if holding:
            if holding.quantity <= transaction.quantity:
                db.delete(holding)
            else:
                # Recalculate average cost
                total_cost_basis = (holding.quantity * holding.average_cost) - transaction.total_amount
                holding.quantity -= transaction.quantity
                holding.average_cost = total_cost_basis / holding.quantity if holding.quantity > 0 else Decimal("0.00")

    elif transaction.transaction_type == TransactionType.SELL:
        # Deduct cash
        total_proceeds = transaction.total_amount - transaction.fees
        current_user.cash_balance -= total_proceeds

        # Restore holding
        holding = db.query(StockHolding).filter(
            StockHolding.user_id == current_user.id,
            StockHolding.symbol == transaction.symbol
        ).first()

        if holding:
            # Add shares back
            total_cost_basis = holding.quantity * holding.average_cost
            holding.quantity += transaction.quantity
            holding.average_cost = total_cost_basis / holding.quantity
        else:
            # Recreate holding (Note: we don't know the original cost basis, so we use transaction price)
            new_holding = StockHolding(
                user_id=current_user.id,
                symbol=transaction.symbol,
                quantity=transaction.quantity,
                average_cost=transaction.price
            )
            db.add(new_holding)

    elif transaction.transaction_type == TransactionType.DEPOSIT:
        current_user.cash_balance -= transaction.total_amount

    elif transaction.transaction_type == TransactionType.WITHDRAWAL:
        current_user.cash_balance += transaction.total_amount

    db.delete(transaction)
    db.commit()

    return None
