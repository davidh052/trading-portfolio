from tests.helpers import money


def add(client, headers, symbol, **extra):
    return client.post("/api/watchlist/", json={"symbol": symbol, **extra}, headers=headers)


def test_add_to_watchlist(client, auth_headers):
    response = add(client, auth_headers, "aapl", target_price=180.5, notes="buy the dip")

    assert response.status_code == 201
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert money(body["target_price"]) == money("180.50")
    assert body["notes"] == "buy the dip"


def test_target_price_is_optional(client, auth_headers):
    response = add(client, auth_headers, "AAPL")

    assert response.status_code == 201
    assert response.json()["target_price"] is None


def test_rejects_duplicate_symbol(client, auth_headers):
    add(client, auth_headers, "AAPL")
    response = add(client, auth_headers, "aapl")

    assert response.status_code == 400
    assert "already in your watchlist" in response.json()["detail"]


def test_different_users_can_watch_same_symbol(client, auth_headers, other_auth_headers):
    add(client, auth_headers, "AAPL")
    response = add(client, other_auth_headers, "AAPL")

    assert response.status_code == 201


def test_list_watchlist_is_per_user(client, auth_headers, other_auth_headers):
    add(client, auth_headers, "AAPL")
    add(client, auth_headers, "MSFT")
    add(client, other_auth_headers, "TSLA")

    symbols = {
        item["symbol"] for item in client.get("/api/watchlist/", headers=auth_headers).json()
    }

    assert symbols == {"AAPL", "MSFT"}


def test_remove_from_watchlist(client, auth_headers):
    item = add(client, auth_headers, "AAPL").json()

    response = client.delete(f"/api/watchlist/{item['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get("/api/watchlist/", headers=auth_headers).json() == []


def test_cannot_remove_another_users_item(client, auth_headers, other_auth_headers):
    item = add(client, auth_headers, "AAPL").json()

    response = client.delete(f"/api/watchlist/{item['id']}", headers=other_auth_headers)

    assert response.status_code == 404
    assert len(client.get("/api/watchlist/", headers=auth_headers).json()) == 1


def test_watchlist_requires_auth(client):
    assert client.get("/api/watchlist/").status_code == 403
