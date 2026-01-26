# Trading Portfolio Tracker

A full-stack real-time stock portfolio tracking application with analytics. Built with Python (FastAPI), React, and PostgreSQL.

## Features

### Core Features
- User authentication and authorization (JWT)
- Multiple portfolio management
- Real-time stock price updates via WebSockets
- Buy/Sell transactions with automatic portfolio updates
- Portfolio performance analytics (total value, gains/losses, returns)
- Transaction history with filtering
- Stock search and watchlist

### Advanced Features (TODO)
- Portfolio performance metrics (Sharpe ratio, beta, diversification score)
- Historical portfolio value charts
- Price alerts for watchlist stocks
- Export portfolio data (CSV, PDF)
- Dark mode

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI (REST API + WebSockets)
- SQLAlchemy (ORM)
- PostgreSQL (Database)
- JWT authentication
- Alembic (Database migrations)

**Frontend:**
- React 18
- React Router (Navigation)
- Zustand (State management)
- Recharts (Data visualization)
- Tailwind CSS (Styling)
- Axios (HTTP client)

**External APIs:**
- Alpha Vantage / YFinn (Stock data)

## Project Structure

```
trading-portfolio-tracker/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Utilities
│   │   └── database.py       # Database configuration
│   ├── tests/                # Backend tests
│   ├── main.py               # FastAPI app entry point
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── hooks/            # Custom React hooks
│   │   └── utils/            # Utilities
│   ├── public/               # Static files
│   └── package.json          # Node dependencies
├── database/
│   ├── schema.sql            # Database schema
│   └── seed.sql              # Sample data
├── docs/                     # Documentation
└── docker-compose.yml        # Docker setup for PostgreSQL
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL)
- Stock API key (Alpha Vantage, YFinn)

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Schema

Key tables:
- `users` - User accounts
- `transactions` - Buy/Sell/Deposit/Withdrawal records
- `stock_holdings` - Current stock positions per portfolio
- `watchlists` - Stocks users are watching

## Development Roadmap

### Phase 1: Core Functionality
- [X] Project setup and structure
- [X] User authentication (register, login, JWT)
- [X] Portfolio CRUD operations
- [X] Transaction management (buy/sell/deposit/withdrawal)
- [X] Basic portfolio analytics

### Phase 2: Real-time Features
- [ ] Stock search integration with external API
- [ ] WebSocket implementation for live prices
- [ ] Real-time portfolio value updates
- [ ] Watchlist with price tracking

### Phase 3: Analytics & Visualization
- [ ] Portfolio performance charts (Recharts)
- [ ] Historical performance tracking
- [ ] Portfolio metrics (Sharpe ratio, returns, etc.)
- [ ] Transaction history with filters

### Phase 4: Polish & Deploy
- [ ] Comprehensive testing (pytest, React Testing Library)
- [ ] Error handling and validation
- [ ] Loading states and UX improvements
- [ ] Deployment (Railway, Render, or AWS)
- [ ] CI/CD pipeline


## Contributing

This is a portfolio project. Feel free to fork and customize for your own use.

