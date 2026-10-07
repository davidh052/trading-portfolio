# Trading Portfolio - Development Commands
# ========================================

.PHONY: help lint lint-fix lint-backend lint-frontend install-lint test

help:
	@echo "Available commands:"
	@echo "  make lint          - Run all linters (backend + frontend)"
	@echo "  make lint-fix      - Run all linters with auto-fix"
	@echo "  make lint-backend  - Run Ruff on Python backend"
	@echo "  make lint-frontend - Run ESLint on React frontend"
	@echo "  make install-lint  - Install linting dependencies"
	@echo "  make test          - Run backend tests with coverage (needs Postgres running)"

# Run all linters
lint: lint-backend lint-frontend

# Run all linters with auto-fix
lint-fix:
	@echo "🔧 Fixing backend..."
	cd backend && python3 -m ruff check --fix . && python3 -m ruff format .
	@echo "🔧 Fixing frontend..."
	cd frontend && npm run lint:fix

# Backend linting with Ruff
lint-backend:
	@echo "🐍 Linting Python backend with Ruff..."
	cd backend && python3 -m ruff check .
	cd backend && python3 -m ruff format --check .

# Frontend linting with ESLint
lint-frontend:
	@echo "⚛️  Linting React frontend with ESLint..."
	cd frontend && npm run lint

# Install linting dependencies
install-lint:
	@echo "📦 Installing backend linting tools..."
	pip3 install ruff
	@echo "📦 Installing frontend linting tools..."
	cd frontend && npm install

# Backend tests (uses the trading_portfolio_test database; start Postgres with docker compose up -d)
test:
	@echo "🧪 Running backend tests..."
	cd backend && python3 -m pytest --cov=app --cov-report=term-missing
