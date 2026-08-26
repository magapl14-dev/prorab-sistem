"""Кейс A: Загрузка фото — только со входом."""


async def test_anonimnyy_put_401(client, seed):
    r = await client.put("/api/v1/photos/local-upload/photos/x.jpg", content=b"xx")
    assert r.status_code == 401


async def test_put_s_tochkami_400(client, seed, db_session):
    from app.models.models import RolePermission

    db_session.add(RolePermission(role="foreman", resource="photos", action="create", allowed=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.put(
        "/api/v1/photos/local-upload/photos/../secret.txt",
        content=b"xx",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


async def test_put_s_tokenom_200(client, seed, db_session):
    from app.models.models import RolePermission

    db_session.add(RolePermission(role="foreman", resource="photos", action="create", allowed=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.put(
        "/api/v1/photos/local-upload/photos/ok.jpg",
        content=b"jpeg-bytes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
