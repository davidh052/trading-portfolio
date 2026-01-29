from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stock_service import stock_service

router = APIRouter()

@router.get("/search")
def search_stocks(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search for stocks by symbol or company name"""
    results = stock_service.search_stocks(query)
    if results is None:
        raise HTTPException(status_code=500, detail="Error searching for stocks")
    return {"results": results, "count": len(results)}

@router.get("/{symbol}/quote")
def get_stock_quote(symbol: str):
    """Get real-time quote for a stock"""
    quote = stock_service.get_stock_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote not found for symbol: {symbol}")
    return quote

@router.get("/{symbol}/history")
def get_stock_history(
    symbol: str,
    period: str = Query("1M", regex="^(1D|1W|1M|3M|6M|1Y|5Y)$")
):
    """Get historical price data for a stock"""
    history = stock_service.get_stock_history(symbol, period)
    if not history:
        raise HTTPException(status_code=404, detail=f"Historical data not found for symbol: {symbol}")
    return history

@router.get("/{symbol}/company")
def get_company_info(symbol: str):
    """Get company information and fundamentals"""
    company = stock_service.get_company_info(symbol)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company information not found for symbol: {symbol}")
    return company
