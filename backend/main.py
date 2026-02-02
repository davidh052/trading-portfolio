from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, stocks, transactions, watchlist, websocket

app = FastAPI(
    title="Trading Portfolio Tracker API",
    description="Real-time stock portfolio tracking and analytics",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

@app.get("/")
def read_root():
    return {"message": "Trading Portfolio Tracker API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
