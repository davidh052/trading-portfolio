from app.services.stock_service import stock_service


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_quote_returns_service_data(client, prices):
    prices["AAPL"] = 123.45
    response = client.get("/api/stocks/AAPL/quote")

    assert response.status_code == 200
    assert response.json()["price"] == 123.45


def test_quote_404_when_symbol_unknown(client, prices):
    response = client.get("/api/stocks/NOPE/quote")

    assert response.status_code == 404


def test_history_rejects_invalid_period(client):
    response = client.get("/api/stocks/AAPL/history?period=2D")

    assert response.status_code == 422


def test_history_passes_period_to_service(client, monkeypatch):
    calls = []

    def fake_history(symbol, period):
        calls.append((symbol, period))
        return {"symbol": symbol, "period": period, "data": []}

    monkeypatch.setattr(stock_service, "get_stock_history", fake_history)
    response = client.get("/api/stocks/AAPL/history?period=1Y")

    assert response.status_code == 200
    assert calls == [("AAPL", "1Y")]


def test_search_requires_query(client):
    response = client.get("/api/stocks/search?query=")

    assert response.status_code == 422


def test_search_returns_results(client, monkeypatch):
    monkeypatch.setattr(
        stock_service, "search_stocks", lambda q: [{"symbol": "AAPL", "name": "Apple Inc."}]
    )
    response = client.get("/api/stocks/search?query=apple")

    assert response.status_code == 200
    assert response.json() == {"results": [{"symbol": "AAPL", "name": "Apple Inc."}], "count": 1}
