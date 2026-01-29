import os
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.stock_holding import StockHolding
from app.models.user import User
from app.services.stock_service import stock_service

router = APIRouter()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Pydantic schemas
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class StockHoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal | None = None
    market_value: Decimal | None = None
    gain_loss: Decimal | None = None
    gain_loss_percentage: Decimal | None = None

    class Config:
        from_attributes = True

class PortfolioResponse(BaseModel):
    cash_balance: Decimal
    holdings: list[StockHoldingResponse]
    total_market_value: Decimal
    total_gain_loss: Decimal
    total_gain_loss_percentage: Decimal
    number_of_holdings: int

class PerformanceResponse(BaseModel):
    total_value: Decimal
    cash_balance: Decimal
    holdings_value: Decimal
    total_gain_loss: Decimal
    total_gain_loss_percentage: Decimal
    number_of_holdings: int

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed"
        )

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile"""
    return current_user

@router.get("/portfolio", response_model=PortfolioResponse)
def get_user_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio with holdings and analytics"""
    # Get holdings
    holdings = db.query(StockHolding).filter(
        StockHolding.user_id == current_user.id
    ).all()

    # Calculate performance metrics
    holdings_response = []
    total_market_value = Decimal("0.00")
    total_cost = Decimal("0.00")

    for holding in holdings:
        # Fetch real-time price from stock service
        quote = stock_service.get_stock_quote(holding.symbol)
        current_price = Decimal(str(quote["price"])) if quote and quote.get("price") else holding.average_cost

        market_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_cost
        gain_loss = market_value - cost_basis
        gain_loss_percentage = (gain_loss / cost_basis * 100) if cost_basis > 0 else Decimal("0.00")

        holdings_response.append(StockHoldingResponse(
            id=holding.id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            average_cost=holding.average_cost,
            current_price=current_price,
            market_value=market_value,
            gain_loss=gain_loss,
            gain_loss_percentage=gain_loss_percentage
        ))

        total_market_value += market_value
        total_cost += cost_basis

    total_gain_loss = total_market_value - total_cost
    total_gain_loss_percentage = (total_gain_loss / total_cost * 100) if total_cost > 0 else Decimal("0.00")

    return PortfolioResponse(
        cash_balance=current_user.cash_balance,
        holdings=holdings_response,
        total_market_value=total_market_value,
        total_gain_loss=total_gain_loss,
        total_gain_loss_percentage=total_gain_loss_percentage,
        number_of_holdings=len(holdings)
    )

@router.get("/performance", response_model=PerformanceResponse)
def get_user_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio performance metrics (total value, gains/losses, etc.)"""
    # Get all holdings
    holdings = db.query(StockHolding).filter(
        StockHolding.user_id == current_user.id
    ).all()

    # Calculate performance
    holdings_value = Decimal("0.00")
    total_cost = Decimal("0.00")

    for holding in holdings:
        # Fetch real-time price from stock service
        quote = stock_service.get_stock_quote(holding.symbol)
        current_price = Decimal(str(quote["price"])) if quote and quote.get("price") else holding.average_cost

        market_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_cost

        holdings_value += market_value
        total_cost += cost_basis

    total_value = current_user.cash_balance + holdings_value
    total_gain_loss = holdings_value - total_cost
    total_gain_loss_percentage = (total_gain_loss / total_cost * 100) if total_cost > 0 else Decimal("0.00")

    return PerformanceResponse(
        total_value=total_value,
        cash_balance=current_user.cash_balance,
        holdings_value=holdings_value,
        total_gain_loss=total_gain_loss,
        total_gain_loss_percentage=total_gain_loss_percentage,
        number_of_holdings=len(holdings)
    )
