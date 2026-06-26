"""
Shared test fixtures. Spins up an in-memory SQLite database for each test,
overrides the get_db dependency, and provides helpers to seed users with
arbitrary roles.

Environment variables are set BEFORE importing the app, so Settings picks up
the SQLite URL and a deterministic SECRET_KEY.
"""
import os
import tempfile

# IMPORTANT: must run before any `from app...` import.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_pytest_runs_only_not_real")
os.environ.setdefault("ENABLE_RATE_LIMITER", "False")
os.environ.setdefault("COOKIE_SECURE", "False")
os.environ.setdefault("COOKIE_SAMESITE", "lax")
# Attachments are written to a throwaway temp dir during tests.
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="lexstudio_test_uploads_"))

import pytest_asyncio
import httpx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService


@pytest_asyncio.fixture
async def db_engine():
    """One engine per test — full schema is dropped between tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    Session = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    """ASGI test client with the get_db dependency overridden to use our in-memory engine."""
    Session = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _make_user(session: AsyncSession, email: str, password: str, role: UserRole) -> User:
    user = User(
        email=email.lower(),
        hashed_password=AuthService.hash_password(password),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session):
    return await _make_user(db_session, "admin@test.com", "AdminPass123!", UserRole.ADMIN)


@pytest_asyncio.fixture
async def lawyer_user(db_session):
    return await _make_user(db_session, "lawyer@test.com", "LawyerPass123!", UserRole.LAWYER)


@pytest_asyncio.fixture
async def other_lawyer_user(db_session):
    return await _make_user(db_session, "lawyer2@test.com", "LawyerPass123!", UserRole.LAWYER)


@pytest_asyncio.fixture
async def assistant_user(db_session):
    return await _make_user(db_session, "assistant@test.com", "AssistPass123!", UserRole.ASSISTANT)


async def login(client: AsyncClient, email: str, password: str) -> str:
    """Helper: log in, return access token. Cookie is stored automatically in the client."""
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
