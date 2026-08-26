"""Кейс A: Вход по PIN."""


async def test_vernyy_pin_otdaet_access_token(client, seed):
    r = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("access_token")
    assert body["user"]["name"] == "Прораб Иван"
    assert body["user"]["role"] == "foreman"


async def test_nevernyy_pin_401(client, seed):
    r = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "0000"},
    )
    assert r.status_code == 401


async def test_me_bez_tokena_401(client, seed):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


async def test_me_s_tokenom_200(client, seed):
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Прораб Иван"
