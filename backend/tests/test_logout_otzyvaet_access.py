"""Кейс A: Выход отзывает access-токен."""


async def test_posle_logout_me_401(client, seed):
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    body = login.json()
    access = body["access_token"]
    refresh = body["refresh_token"]
    headers = {"Authorization": f"Bearer {access}"}
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200

    out = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers=headers,
    )
    assert out.status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
