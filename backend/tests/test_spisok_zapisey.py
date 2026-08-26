"""Кейс A: Список записей проекта."""


async def test_spisok_bez_tokena_401(client, seed):
    r = await client.get("/api/v1/projects/alpha/records")
    assert r.status_code == 401


async def test_spisok_s_pravom_view_soderzhit_zapis(client, seed):
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/projects/alpha/records",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    names = [item["name"] for item in body["items"]]
    assert "Цемент" in names
