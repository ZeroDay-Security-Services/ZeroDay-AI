async def test_register_creates_user(async_client):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "analyst@zeroday.dev",
            "full_name": "SOC Analyst",
            "password": "supersecret123",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "analyst@zeroday.dev"
    assert "hashed_password" not in body


async def test_register_duplicate_email_rejected(async_client):
    payload = {
        "email": "dupe@zeroday.dev",
        "full_name": "Dupe",
        "password": "supersecret123",
    }
    first = await async_client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await async_client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"


async def test_login_and_me_flow(async_client):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@zeroday.dev",
            "full_name": "Login User",
            "password": "correcthorse123",
        },
    )

    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "login@zeroday.dev", "password": "correcthorse123"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "login@zeroday.dev"


async def test_login_wrong_password_rejected(async_client):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@zeroday.dev",
            "full_name": "User",
            "password": "correcthorse123",
        },
    )
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@zeroday.dev", "password": "incorrect"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_me_without_token_rejected(async_client):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_token_flow(async_client):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@zeroday.dev",
            "full_name": "Refresh User",
            "password": "correcthorse123",
        },
    )
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@zeroday.dev", "password": "correcthorse123"},
    )
    refresh_token = login.json()["refresh_token"]

    refreshed = await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()
