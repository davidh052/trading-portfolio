"""
Shared test fixtures.

Tests run against a real PostgreSQL database built from database/schema.sql, so they
exercise the same constraints, enums and types as production. External stock data is
mocked so tests are fast and deterministic.
"""

import os
from pathlib import Path

# Must be configured before the app is imported (auth.py reads SECRET_KEY at import time,
# database.py creates the engine at import time).
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/trading_portfolio_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import psycopg2  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.database import engine  # noqa: E402
from app.services.stock_service import stock_service  # noqa: E402
from main import app  # noqa: E402
from tests.helpers import register_and_login  # noqa: E402

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "database" / "schema.sql"
TABLES = ["transactions", "stock_holdings", "watchlists", "users"]


def _ensure_test_database_exists():
    """Create the test database if it doesn't exist (convenient for local runs)."""
    url = make_url(TEST_DATABASE_URL)
    conn = psycopg2.connect(
        host=url.host,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        dbname="postgres",
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{url.database}"')
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def database():
    """Rebuild the schema once per test session."""
    _ensure_test_database_exists()
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            cur.execute(SCHEMA_PATH.read_text())
        raw.commit()
    finally:
        raw.close()
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables():
    """Wipe all rows after each test so tests are independent."""
    yield
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
        raw.commit()
    finally:
        raw.close()


@pytest.fixture
def prices(monkeypatch):
    """
    Mock market prices. Tests set prices with `prices["AAPL"] = 100`.
    Symbols without a price behave like the real service when a quote can't be found.
    """
    current = {}

    def fake_quote(symbol):
        price = current.get(symbol.upper())
        if price is None:
            return None
        return {"symbol": symbol.upper(), "price": price}

    monkeypatch.setattr(stock_service, "get_stock_quote", fake_quote)
    return current


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    return register_and_login(client)


@pytest.fixture
def other_auth_headers(client):
    return register_and_login(client, email="bob@example.com", username="bob")
