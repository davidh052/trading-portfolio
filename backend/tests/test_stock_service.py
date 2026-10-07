"""
Unit tests for StockService. yfinance and HTTP calls are mocked so these never hit the network.
"""

import pandas as pd
import pytest

from app.services import stock_service as stock_service_module
from app.services.stock_service import StockService


class FakeTicker:
    def __init__(self, info=None, history=None):
        self.info = info
        self._history = history
        self.history_periods = []

    def history(self, period):
        self.history_periods.append(period)
        return self._history


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture
def ticker(monkeypatch):
    """Make yf.Ticker return a FakeTicker; tests configure it via the returned object."""
    fake = FakeTicker()
    monkeypatch.setattr(stock_service_module.yf, "Ticker", lambda symbol: fake)
    return fake


@pytest.fixture
def http(monkeypatch):
    """Capture requests.get calls and return a configurable JSON payload."""
    state = {"data": {}, "calls": []}

    def fake_get(url, params=None, **kwargs):
        state["calls"].append((url, params))
        if isinstance(state["data"], Exception):
            raise state["data"]
        return FakeResponse(state["data"])

    monkeypatch.setattr(stock_service_module.requests, "get", fake_get)
    return state


# --- Quotes ------------------------------------------------------------------


def test_quote_from_yfinance(ticker, http):
    ticker.info = {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "currentPrice": 110.0,
        "previousClose": 100.0,
        "volume": 1000,
        "marketCap": 3_000_000,
    }

    quote = StockService.get_stock_quote("aapl")

    assert quote["symbol"] == "AAPL"
    assert quote["name"] == "Apple Inc."
    assert quote["price"] == 110.0
    assert quote["change"] == 10.0
    assert quote["change_percent"] == 10.0
    assert quote["volume"] == 1000
    assert http["calls"] == []  # no fallback needed


def test_quote_uses_regular_market_fields_as_fallback(ticker, http):
    ticker.info = {
        "symbol": "SPY",
        "shortName": "SPDR S&P 500",
        "regularMarketPrice": 50.0,
        "regularMarketPreviousClose": 40.0,
    }

    quote = StockService.get_stock_quote("SPY")

    assert quote["name"] == "SPDR S&P 500"
    assert quote["price"] == 50.0
    assert quote["previous_close"] == 40.0
    assert quote["change_percent"] == 25.0


def test_quote_falls_back_to_alpha_vantage(ticker, http):
    ticker.info = {}  # yfinance has nothing for this symbol
    http["data"] = {
        "Global Quote": {
            "01. symbol": "IBM",
            "02. open": "99.00",
            "03. high": "101.00",
            "04. low": "98.00",
            "05. price": "100.50",
            "06. volume": "12345",
            "08. previous close": "99.50",
            "09. change": "1.00",
            "10. change percent": "1.005%",
        }
    }

    quote = StockService.get_stock_quote("IBM")

    assert quote["symbol"] == "IBM"
    assert quote["price"] == 100.5
    assert quote["change_percent"] == 1.005
    assert quote["volume"] == 12345
    assert http["calls"][0][1]["symbol"] == "IBM"


def test_quote_returns_none_when_all_sources_fail(ticker, http):
    ticker.info = {}
    http["data"] = {}

    assert StockService.get_stock_quote("NOPE") is None


def test_quote_returns_none_when_backup_errors(ticker, http):
    ticker.info = {}
    http["data"] = ConnectionError("network down")

    assert StockService.get_stock_quote("NOPE") is None


# --- Search ------------------------------------------------------------------


def test_search_keeps_only_stocks_and_etfs(http):
    http["data"] = {
        "quotes": [
            {"symbol": "AAPL", "longname": "Apple Inc.", "quoteType": "EQUITY", "exchange": "NMS"},
            {"symbol": "SPY", "shortname": "SPDR S&P 500", "quoteType": "ETF", "exchange": "PCX"},
            {"symbol": "AAPL240119C00100000", "quoteType": "OPTION"},
            {"symbol": "BTC-USD", "quoteType": "CRYPTOCURRENCY"},
        ]
    }

    results = StockService.search_stocks("a")

    assert [r["symbol"] for r in results] == ["AAPL", "SPY"]
    assert results[0]["name"] == "Apple Inc."
    assert results[1]["name"] == "SPDR S&P 500"
    assert results[0]["region"] == "NMS"


def test_search_returns_empty_list_on_error(http):
    http["data"] = ConnectionError("network down")

    assert StockService.search_stocks("apple") == []


# --- History -----------------------------------------------------------------


def make_history():
    return pd.DataFrame(
        {
            "Open": [1.111, 2.0],
            "High": [1.5, 2.5],
            "Low": [1.0, 1.9],
            "Close": [1.234, 2.345],
            "Volume": [100, 200],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-05"]),
    )


@pytest.mark.parametrize(
    ("period", "yf_period"),
    [("1D", "1d"), ("1W", "5d"), ("1M", "1mo"), ("1Y", "1y"), ("5Y", "5y")],
)
def test_history_maps_period(ticker, period, yf_period):
    ticker._history = make_history()

    StockService.get_stock_history("AAPL", period)

    assert ticker.history_periods == [yf_period]


def test_history_formats_rows(ticker):
    ticker._history = make_history()

    history = StockService.get_stock_history("aapl", "1M")

    assert history["symbol"] == "AAPL"
    assert history["period"] == "1M"
    assert history["data"][0] == {
        "date": "2026-01-02",
        "open": 1.11,
        "high": 1.5,
        "low": 1.0,
        "close": 1.23,
        "volume": 100,
    }
    assert len(history["data"]) == 2


def test_history_returns_none_when_empty(ticker):
    ticker._history = pd.DataFrame()

    assert StockService.get_stock_history("NOPE", "1M") is None


# --- Company info ------------------------------------------------------------


def test_company_info(ticker):
    ticker.info = {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "sector": "Technology",
        "fullTimeEmployees": 160000,
        "fiftyTwoWeekHigh": 200.0,
    }

    info = StockService.get_company_info("aapl")

    assert info["symbol"] == "AAPL"
    assert info["sector"] == "Technology"
    assert info["employees"] == 160000
    assert info["52_week_high"] == 200.0


def test_company_info_returns_none_for_unknown_symbol(ticker):
    ticker.info = {}

    assert StockService.get_company_info("NOPE") is None
