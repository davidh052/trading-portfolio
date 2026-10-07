from tests.helpers import deposit, money, portfolio, trade


def test_empty_portfolio(client, auth_headers):
    body = portfolio(client, auth_headers)

    assert money(body["cash_balance"]) == money("0")
    assert body["holdings"] == []
    assert body["number_of_holdings"] == 0
    assert money(body["total_gain_loss"]) == money("0")


def test_portfolio_values_holdings_at_current_price(client, auth_headers, prices):
    deposit(client, auth_headers, 10000)
    prices["AAPL"] = 100
    prices["MSFT"] = 200
    trade(client, auth_headers, "BUY", "AAPL", 10)  # cost 1000
    trade(client, auth_headers, "BUY", "MSFT", 5)  # cost 1000
    prices["AAPL"] = 150  # +500
    prices["MSFT"] = 180  # -100

    body = portfolio(client, auth_headers)

    assert body["number_of_holdings"] == 2
    assert money(body["cash_balance"]) == money("8000.00")
    assert money(body["total_market_value"]) == money("2400")
    assert money(body["total_gain_loss"]) == money("400")
    assert money(body["total_gain_loss_percentage"]) == money("20")

    aapl = next(h for h in body["holdings"] if h["symbol"] == "AAPL")
    assert money(aapl["current_price"]) == money("150")
    assert money(aapl["market_value"]) == money("1500")
    assert money(aapl["gain_loss"]) == money("500")
    assert money(aapl["gain_loss_percentage"]) == money("50")


def test_portfolio_falls_back_to_cost_when_price_unavailable(client, auth_headers, prices):
    deposit(client, auth_headers, 1000)
    prices["AAPL"] = 100
    trade(client, auth_headers, "BUY", "AAPL", 2)
    del prices["AAPL"]

    holding = portfolio(client, auth_headers)["holdings"][0]

    assert money(holding["current_price"]) == money("100")
    assert money(holding["gain_loss"]) == money("0")


def test_performance_includes_cash_in_total_value(client, auth_headers, prices):
    deposit(client, auth_headers, 1000)
    prices["AAPL"] = 100
    trade(client, auth_headers, "BUY", "AAPL", 4)  # cash 600, cost 400
    prices["AAPL"] = 110  # holdings 440

    response = client.get("/api/auth/performance", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert money(body["cash_balance"]) == money("600.00")
    assert money(body["holdings_value"]) == money("440")
    assert money(body["total_value"]) == money("1040")
    assert money(body["total_gain_loss"]) == money("40")
    assert money(body["total_gain_loss_percentage"]) == money("10")


def test_portfolios_are_isolated_between_users(client, auth_headers, other_auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "AAPL", 1)

    other = portfolio(client, other_auth_headers)
    assert other["holdings"] == []
    assert money(other["cash_balance"]) == money("0")
