"""
Neolysis Test Suite — pytest Configuration & Shared Fixtures
=============================================================

Fixtures:
    client        : Async HTTPX test client for FastAPI
    db_session    : In-memory async SQLite session (fast, no network needed)
    mock_db       : Pre-configured MagicMock for unit tests
    sample_smiles : Dict of SMILES strings for common test compounds

Usage:
    pytest tests/ -v --asyncio-mode=auto
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

# Override DB to in-memory SQLite before app import
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("QDRANT_PORT", "6333")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from app.db.session import Base, get_db  # noqa: E402
from main import app  # noqa: E402


# ── In-memory SQLite engine (test isolation) ───────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables once per test session."""
    # Import all models so metadata is populated
    import app.models  # noqa: F401
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide a test DB session with automatic rollback after each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Async HTTPX client that uses the test DB session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_db():
    """MagicMock for unit tests that don't need a real DB session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_smiles():
    """Dictionary of well-known SMILES strings for testing."""
    return {
        "aspirin":    "CC(=O)Oc1ccccc1C(=O)O",
        "quercetin":  "O=c1c(O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12",
        "ibuprofen":  "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "invalid":    "XXXNOTASMILES",
        "empty":      "",
        "caffeine":   "Cn1cnc2c1c(=O)n(c(=O)n2C)C",
        "chloroquine":"ClC1=CC=NC2=CC(=CC=C12)NC(C)CCCN(CC)CC",
    }
