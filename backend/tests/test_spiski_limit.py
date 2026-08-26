"""Кейс A: Списки с limit, тело по-прежнему массив."""
from uuid import uuid4

from tests.conftest import hash_pin
from app.models.models import Master, RolePermission, User


async def test_masters_limit_rezhet_massiv(client, seed, db_session):
    db_session.add(RolePermission(role="foreman", resource="master_payments", action="view", allowed=True))
    for name in ("Алексей", "Борис", "Виктор"):
        db_session.add(Master(id=uuid4(), name=name, active=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79001112233", "pin": "1234"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    full = await client.get("/api/v1/masters", headers=headers)
    assert full.status_code == 200
    assert isinstance(full.json(), list)
    assert len(full.json()) >= 3
    clipped = await client.get("/api/v1/masters?limit=1&offset=0", headers=headers)
    assert clipped.status_code == 200
    assert isinstance(clipped.json(), list)
    assert len(clipped.json()) == 1
    assert int(clipped.headers["x-total-count"]) >= 3


async def test_admin_users_limit(client, seed, db_session):
    admin = User(
        id=uuid4(),
        phone="+79000000001",
        name="Админ",
        pin_hash=hash_pin("1234"),
        role="admin",
        active=True,
    )
    db_session.add(admin)
    db_session.add(RolePermission(role="admin", resource="users", action="view", allowed=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+79000000001", "pin": "1234"},
    )
    token = login.json()["access_token"]
    r = await client.get("/api/v1/admin/users?limit=1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 1
    assert int(r.headers["x-total-count"]) >= 2
