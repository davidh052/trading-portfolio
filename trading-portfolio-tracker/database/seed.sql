-- Sample data for development and testing

-- Sample user (password is 'password123' hashed with bcrypt)
INSERT INTO users (email, username, hashed_password, full_name) VALUES
('demo@example.com', 'demouser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNGw7Jb5m', 'Demo User');

-- Sample portfolio for demo user
INSERT INTO portfolios (user_id, name, description, cash_balance) VALUES
(1, 'Main Portfolio', 'My primary investment portfolio', 10000.00),
(1, 'Tech Stocks', 'Technology sector focused portfolio', 5000.00);

-- Sample transactions
INSERT INTO transactions (portfolio_id, transaction_type, symbol, quantity, price, total_amount, fees, notes) VALUES
-- Initial deposit
(1, 'DEPOSIT', NULL, NULL, NULL, 10000.00, 0.00, 'Initial deposit'),
-- Stock purchases
(1, 'BUY', 'AAPL', 10, 150.00, 1500.00, 1.00, 'Apple Inc'),
(1, 'BUY', 'GOOGL', 5, 120.00, 600.00, 1.00, 'Alphabet Inc'),
(1, 'BUY', 'MSFT', 8, 300.00, 2400.00, 1.00, 'Microsoft Corp');

-- Sample stock holdings (calculated from transactions)
INSERT INTO stock_holdings (portfolio_id, symbol, quantity, average_cost) VALUES
(1, 'AAPL', 10, 150.00),
(1, 'GOOGL', 5, 120.00),
(1, 'MSFT', 8, 300.00);

-- Sample watchlist
INSERT INTO watchlists (user_id, symbol, target_price, notes) VALUES
(1, 'TSLA', 200.00, 'Waiting for better entry point'),
(1, 'NVDA', 450.00, 'Interested in AI exposure'),
(1, 'AMD', 100.00, 'Good value play');

-- Update portfolio cash balance after transactions
UPDATE portfolios SET cash_balance = 10000.00 - 1500.00 - 600.00 - 2400.00 - 3.00 WHERE id = 1;
