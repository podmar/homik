from httpx import AsyncClient


async def test_register_creates_user(client: AsyncClient):
    resp = await client.post(
        "/auth/register", json={"email": "alice@test.com", "password": "testpass123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@test.com"
    assert "password" not in body


async def test_register_duplicate_email_returns_400(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "alice@test.com", "password": "testpass123"}
    )
    resp = await client.post(
        "/auth/register", json={"email": "alice@test.com", "password": "testpass123"}
    )
    assert resp.status_code == 400


async def test_register_invalid_email_returns_422(client: AsyncClient):
    resp = await client.post(
        "/auth/register", json={"email": "not-an-email", "password": "testpass123"}
    )
    assert resp.status_code == 422


async def test_login_returns_token(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "alice@test.com", "password": "testpass123"}
    )
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": "alice@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password_returns_400(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "alice@test.com", "password": "testpass123"}
    )
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": "alice@test.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 400


async def test_login_unknown_email_returns_400(client: AsyncClient):
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": "nobody@test.com", "password": "testpass123"},
    )
    assert resp.status_code == 400
