"""Кейс A: Отказ без права view."""


async def test_net_view_na_kinds_403(client, seed):
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79007778899", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/projects/alpha/records",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


async def test_net_dostupa_k_proektu_403(client, seed):
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79004445566", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/projects/alpha/records",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert "project" in r.json()["detail"].lower()
