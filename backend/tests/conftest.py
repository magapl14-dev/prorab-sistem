"""S1 characterization: in-memory DB + FakeRedis. Product code unchanged."""
from __future__ import annotations

import os
import tempfile
from datetime import date
from uuid import uuid4

os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="welldom-test-uploads-"))
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_32_chars_minimum_x")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("REDIS_ENABLED", "false")
os.environ.setdefault("STORAGE_TYPE", "local")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

import bcrypt

from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app
from app.models import models  # noqa: F401 — register metadata
from app.models.models import Project, Record, RolePermission, User, UserProject


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(PGUUID, "sqlite")
def _uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))


@pytest.fixture(autouse=True)
def _pin_compat(monkeypatch):
    """passlib+bcrypt 5 ломает hash; HTTP-контракт тот же."""
    monkeypatch.setattr("app.core.security.hash_pin", hash_pin)
    monkeypatch.setattr("app.core.security.verify_pin", verify_pin)
    monkeypatch.setattr("app.api.v1.auth.hash_pin", hash_pin)
    monkeypatch.setattr("app.api.v1.auth.verify_pin", verify_pin)


class FakeRedis:
    def __init__(self):
        self._store: dict = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value):
        self._store[key] = value

    async def setex(self, key, ttl, value):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)

    async def incr(self, key):
        self._store[key] = int(self._store.get(key) or 0) + 1
        return self._store[key]

    async def expire(self, key, ttl):
        return True


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest_asyncio.fixture
async def client(db_session, fake_redis):
    async def _get_db():
        yield db_session

    async def _get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis] = _get_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed(db_session):
    project = Project(id=uuid4(), code="alpha", name="Альфа")
    foreman = User(
        id=uuid4(),
        phone="+79001112233",
        name="Прораб Иван",
        pin_hash=hash_pin("1234"),
        role="foreman",
        active=True,
    )
    outsider = User(
        id=uuid4(),
        phone="+79004445566",
        name="Чужой",
        pin_hash=hash_pin("1234"),
        role="foreman",
        active=True,
    )
    no_view = User(
        id=uuid4(),
        phone="+79007778899",
        name="Без прав",
        pin_hash=hash_pin("1234"),
        role="client",
        active=True,
    )
    db_session.add_all([project, foreman, outsider, no_view])
    await db_session.flush()
    db_session.add(UserProject(user_id=foreman.id, project_id=project.id, role="foreman"))
    db_session.add(UserProject(user_id=no_view.id, project_id=project.id, role="client"))
    db_session.add(RolePermission(role="foreman", resource="expenses", action="view", allowed=True))
    db_session.add(
        Record(
            id=uuid4(),
            project_id=project.id,
            kind="expense",
            operation_date=date(2026, 8, 1),
            name="Цемент",
            author_id=foreman.id,
        )
    )
    await db_session.commit()
    return {
        "project": project,
        "foreman": foreman,
        "outsider": outsider,
        "no_view": no_view,
    }


async def login(client: AsyncClient, phone: str, pin: str = "1234"):
    return await client.post("/api/v1/auth/login", json={"phone": phone, "pin": pin})
