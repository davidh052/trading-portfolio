-- Trading Portfolio Tracker Database Schema

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    cash_balance DECIMAL(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Transactions table
CREATE TYPE transaction_type AS ENUM ('BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL');

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_type transaction_type NOT NULL,
    symbol VARCHAR(10),  -- NULL for DEPOSIT/WITHDRAWAL
    quantity DECIMAL(15, 4),  -- Number of shares
    price DECIMAL(15, 2),  -- Price per share
    total_amount DECIMAL(15, 2) NOT NULL,
    fees DECIMAL(15, 2) DEFAULT 0.00,
    notes TEXT,
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);

-- Stock holdings table (current positions)
CREATE TABLE stock_holdings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    quantity DECIMAL(15, 4) NOT NULL,
    average_cost DECIMAL(15, 2) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)  -- One holding per symbol per user
);

CREATE INDEX idx_holdings_user_id ON stock_holdings(user_id);
CREATE INDEX idx_holdings_symbol ON stock_holdings(symbol);

-- Watchlist table
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    target_price DECIMAL(15, 2),  -- Optional price alert
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)  -- Prevent duplicate symbols per user
);

CREATE INDEX idx_watchlist_user_id ON watchlists(user_id);
CREATE INDEX idx_watchlist_symbol ON watchlists(symbol);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holdings_updated_at BEFORE UPDATE ON stock_holdings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
