from decimal import Decimal


def register_and_login(client, email="alice@example.com", username="alice"):
    """Register a user and return auth headers for them."""
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": username,
            "full_name": "Test User",
            "password": "password123",
        },
    )
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def money(value):
    """Decimals are serialized as strings in JSON; compare them exactly."""
    return Decimal(str(value))


def deposit(client, headers, amount):
    response = client.post(
        "/api/transactions/",
        json={"transaction_type": "DEPOSIT", "total_amount": amount},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def trade(client, headers, transaction_type, symbol, quantity, **extra):
    return client.post(
        "/api/transactions/",
        json={
            "transaction_type": transaction_type,
            "symbol": symbol,
            "quantity": quantity,
            **extra,
        },
        headers=headers,
    )


def portfolio(client, headers):
    response = client.get("/api/auth/portfolio", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def holding(client, headers, symbol):
    """Return the holding for a symbol, or None if the user doesn't own it."""
    holdings = portfolio(client, headers)["holdings"]
    return next((h for h in holdings if h["symbol"] == symbol), None)
