from datetime import timedelta

from app.api.auth import create_access_token

USER = {
    "email": "alice@example.com",
    "username": "alice",
    "full_name": "Alice Smith",
    "password": "password123",
}


def register(client, **overrides):
    return client.post("/api/auth/register", json={**USER, **overrides})


def test_register_creates_user(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER["email"]
    assert body["username"] == USER["username"]
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client):
    register(client)
    response = register(client, username="someone_else")

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_rejects_duplicate_username(client):
    register(client)
    response = register(client, email="other@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"


def test_register_rejects_invalid_email(client):
    response = register(client, email="not-an-email")

    assert response.status_code == 422


def test_login_returns_token(client):
    register(client)
    response = client.post(
        "/api/auth/login", json={"email": USER["email"], "password": USER["password"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == USER["email"]


def test_login_rejects_wrong_password(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong"})

    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "password123"}
    )

    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


def test_me_requires_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 403


def test_me_rejects_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_rejects_expired_token(client, auth_headers):
    token = create_access_token({"sub": "alice@example.com"}, expires_delta=timedelta(minutes=-1))
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_me_rejects_token_for_deleted_user(client):
    token = create_access_token({"sub": "ghost@example.com"})
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
