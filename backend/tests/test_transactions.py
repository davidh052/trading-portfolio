from tests.helpers import deposit, holding, money, portfolio, trade


def cash(client, headers):
    return money(portfolio(client, headers)["cash_balance"])


# --- Cash transactions -------------------------------------------------------


def test_deposit_increases_cash(client, auth_headers):
    deposit(client, auth_headers, 1000)

    assert cash(client, auth_headers) == money("1000.00")


def test_withdrawal_decreases_cash(client, auth_headers):
    deposit(client, auth_headers, 1000)
    response = client.post(
        "/api/transactions/",
        json={"transaction_type": "WITHDRAWAL", "total_amount": 250},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert cash(client, auth_headers) == money("750.00")


def test_withdrawal_rejects_overdraft(client, auth_headers):
    deposit(client, auth_headers, 100)
    response = client.post(
        "/api/transactions/",
        json={"transaction_type": "WITHDRAWAL", "total_amount": 101},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert cash(client, auth_headers) == money("100.00")


def test_deposit_requires_positive_amount(client, auth_headers):
    for body in [{}, {"total_amount": 0}, {"total_amount": -5}]:
        response = client.post(
            "/api/transactions/",
            json={"transaction_type": "DEPOSIT", **body},
            headers=auth_headers,
        )
        assert response.status_code == 422, body


# --- Buying ------------------------------------------------------------------


def test_buy_executes_at_server_market_price(client, auth_headers, prices):
    prices["AAPL"] = 150
    deposit(client, auth_headers, 1000)

    # Client tries to set its own price and total; both must be ignored
    response = trade(client, auth_headers, "BUY", "AAPL", 2, price=1, total_amount=2)

    assert response.status_code == 201
    tx = response.json()
    assert money(tx["price"]) == money("150.00")
    assert money(tx["total_amount"]) == money("300.00")
    assert cash(client, auth_headers) == money("700.00")


def test_buy_creates_holding(client, auth_headers, prices):
    prices["AAPL"] = 150
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "aapl", 2)

    h = holding(client, auth_headers, "AAPL")
    assert money(h["quantity"]) == money("2")
    assert money(h["average_cost"]) == money("150.00")


def test_buy_twice_averages_cost(client, auth_headers, prices):
    deposit(client, auth_headers, 10000)
    prices["AAPL"] = 100
    trade(client, auth_headers, "BUY", "AAPL", 10)
    prices["AAPL"] = 200
    trade(client, auth_headers, "BUY", "AAPL", 30)

    # (10 * 100 + 30 * 200) / 40 = 175
    h = holding(client, auth_headers, "AAPL")
    assert money(h["quantity"]) == money("40")
    assert money(h["average_cost"]) == money("175.00")


def test_buy_deducts_fees(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "AAPL", 1, fees=5)

    assert cash(client, auth_headers) == money("895.00")


def test_buy_rejects_insufficient_cash(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 99)
    response = trade(client, auth_headers, "BUY", "AAPL", 1)

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient cash balance"
    assert cash(client, auth_headers) == money("99.00")
    assert holding(client, auth_headers, "AAPL") is None


def test_buy_fails_when_price_unavailable(client, auth_headers, prices):
    deposit(client, auth_headers, 1000)
    response = trade(client, auth_headers, "BUY", "NOPE", 1)

    assert response.status_code == 404
    assert cash(client, auth_headers) == money("1000.00")


def test_buy_requires_symbol_and_positive_quantity(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)

    bad_requests = [
        {"transaction_type": "BUY", "quantity": 1},
        {"transaction_type": "BUY", "symbol": "AAPL"},
        {"transaction_type": "BUY", "symbol": "AAPL", "quantity": 0},
        {"transaction_type": "BUY", "symbol": "AAPL", "quantity": -1},
    ]
    for body in bad_requests:
        response = client.post("/api/transactions/", json=body, headers=auth_headers)
        assert response.status_code == 422, body


# --- Selling -----------------------------------------------------------------


def test_sell_adds_proceeds_and_reduces_holding(client, auth_headers, prices):
    deposit(client, auth_headers, 1000)
    prices["AAPL"] = 100
    trade(client, auth_headers, "BUY", "AAPL", 5)
    prices["AAPL"] = 120
    response = trade(client, auth_headers, "SELL", "AAPL", 2)

    assert response.status_code == 201
    # 1000 - 500 + 240
    assert cash(client, auth_headers) == money("740.00")
    h = holding(client, auth_headers, "AAPL")
    assert money(h["quantity"]) == money("3")
    # Selling doesn't change the cost basis of the remaining shares
    assert money(h["average_cost"]) == money("100.00")


def test_sell_entire_position_removes_holding(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "AAPL", 5)
    trade(client, auth_headers, "SELL", "AAPL", 5)

    assert holding(client, auth_headers, "AAPL") is None
    assert cash(client, auth_headers) == money("1000.00")


def test_sell_deducts_fees_from_proceeds(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "AAPL", 5)
    trade(client, auth_headers, "SELL", "AAPL", 5, fees=3)

    assert cash(client, auth_headers) == money("997.00")


def test_sell_rejects_more_shares_than_owned(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "AAPL", 2)
    response = trade(client, auth_headers, "SELL", "AAPL", 3)

    assert response.status_code == 400
    assert "Insufficient shares" in response.json()["detail"]
    assert money(holding(client, auth_headers, "AAPL")["quantity"]) == money("2")


def test_sell_rejects_stock_not_owned(client, auth_headers, prices):
    prices["AAPL"] = 100
    response = trade(client, auth_headers, "SELL", "AAPL", 1)

    assert response.status_code == 400
    assert "No holdings found" in response.json()["detail"]


def test_supports_fractional_shares(client, auth_headers, prices):
    prices["AAPL"] = 200
    deposit(client, auth_headers, 1000)
    response = trade(client, auth_headers, "BUY", "AAPL", 0.5)

    assert response.status_code == 201
    assert money(holding(client, auth_headers, "AAPL")["quantity"]) == money("0.5")
    assert cash(client, auth_headers) == money("900.00")


# --- Listing / fetching ------------------------------------------------------


def test_list_returns_newest_first(client, auth_headers):
    deposit(client, auth_headers, 100)
    deposit(client, auth_headers, 200)
    response = client.get("/api/transactions/", headers=auth_headers)

    assert response.status_code == 200
    amounts = [money(tx["total_amount"]) for tx in response.json()]
    assert amounts == [money("200.00"), money("100.00")]


def test_users_only_see_their_own_transactions(client, auth_headers, other_auth_headers):
    tx = deposit(client, auth_headers, 100)

    assert client.get("/api/transactions/", headers=other_auth_headers).json() == []
    response = client.get(f"/api/transactions/{tx['id']}", headers=other_auth_headers)
    assert response.status_code == 404


def test_get_transaction_by_id(client, auth_headers):
    tx = deposit(client, auth_headers, 100)
    response = client.get(f"/api/transactions/{tx['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == tx["id"]


def test_transactions_require_auth(client):
    assert client.get("/api/transactions/").status_code == 403
    assert client.post("/api/transactions/", json={}).status_code == 403


# --- Deleting (reverses the transaction's effects) ---------------------------


def delete(client, headers, tx_id):
    response = client.delete(f"/api/transactions/{tx_id}", headers=headers)
    assert response.status_code == 204, response.text


def test_delete_deposit_removes_cash(client, auth_headers):
    deposit(client, auth_headers, 500)
    tx = deposit(client, auth_headers, 200)
    delete(client, auth_headers, tx["id"])

    assert cash(client, auth_headers) == money("500.00")


def test_delete_buy_refunds_cash_and_restores_cost_basis(client, auth_headers, prices):
    deposit(client, auth_headers, 10000)
    prices["AAPL"] = 100
    trade(client, auth_headers, "BUY", "AAPL", 10)
    prices["AAPL"] = 200
    second = trade(client, auth_headers, "BUY", "AAPL", 10).json()

    delete(client, auth_headers, second["id"])

    assert cash(client, auth_headers) == money("9000.00")
    h = holding(client, auth_headers, "AAPL")
    assert money(h["quantity"]) == money("10")
    assert money(h["average_cost"]) == money("100.00")


def test_delete_only_buy_removes_holding(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    tx = trade(client, auth_headers, "BUY", "AAPL", 3).json()
    delete(client, auth_headers, tx["id"])

    assert holding(client, auth_headers, "AAPL") is None
    assert cash(client, auth_headers) == money("1000.00")


def test_delete_sell_restores_shares_and_removes_proceeds(client, auth_headers, prices):
    deposit(client, auth_headers, 1000)
    prices["AAPL"] = 100
    trade(client, auth_headers, "BUY", "AAPL", 5)
    prices["AAPL"] = 150
    sell = trade(client, auth_headers, "SELL", "AAPL", 2).json()

    delete(client, auth_headers, sell["id"])

    assert cash(client, auth_headers) == money("500.00")
    assert money(holding(client, auth_headers, "AAPL")["quantity"]) == money("5")


def test_delete_sell_of_entire_position_recreates_holding(client, auth_headers, prices):
    prices["AAPL"] = 100
    deposit(client, auth_headers, 1000)
    trade(client, auth_headers, "BUY", "AAPL", 5)
    sell = trade(client, auth_headers, "SELL", "AAPL", 5).json()

    delete(client, auth_headers, sell["id"])

    h = holding(client, auth_headers, "AAPL")
    assert money(h["quantity"]) == money("5")
    assert cash(client, auth_headers) == money("500.00")


def test_cannot_delete_another_users_transaction(client, auth_headers, other_auth_headers):
    tx = deposit(client, auth_headers, 100)
    response = client.delete(f"/api/transactions/{tx['id']}", headers=other_auth_headers)

    assert response.status_code == 404
    assert cash(client, auth_headers) == money("100.00")
