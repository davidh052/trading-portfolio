from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter()


class WatchlistCreate(BaseModel):
    symbol: str
    target_price: Decimal | None = None
    notes: str | None = None


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    target_price: Decimal | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a stock to the user's watchlist"""
    symbol = watchlist_data.symbol.upper()

    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{symbol} is already in your watchlist"
        )

    new_item = Watchlist(
        user_id=current_user.id,
        symbol=symbol,
        target_price=watchlist_data.target_price,
        notes=watchlist_data.notes
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@router.get("/", response_model=list[WatchlistResponse])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all watchlist items for user"""
    items = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).order_by(Watchlist.created_at.desc()).all()

    return items


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a stock from the user's watchlist"""
    item = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found"
        )

    db.delete(item)
    db.commit()

    return None
