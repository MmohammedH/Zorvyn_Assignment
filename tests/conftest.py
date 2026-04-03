"""
Test configuration — fully mocked, no real database.

get_db is overridden with an AsyncMock session.
Individual tests patch service functions as needed.
get_current_user is overridden per-test via app.dependency_overrides.
"""
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from httpx import ASGITransport, AsyncClient

from clients.db.connection import get_db
from handlers.auth_handlers import get_current_user
from handlers.error_handlers import setup_error_handlers
from middleware.request_logging import RequestLoggingMiddleware


# ── Reusable mock users ───────────────────────────────────────────────────────

def mock_user(role: str = "viewer", user_id: int = 1) -> MagicMock:
    u = MagicMock()
    u.id = user_id
    u.email = f"{role}@test.com"
    u.full_name = f"Test {role.title()}"
    u.role = role
    u.is_active = True
    u.created_at = datetime(2026, 1, 1)
    u.updated_at = datetime(2026, 1, 1)
    return u


VIEWER = mock_user("viewer", 1)
ANALYST = mock_user("analyst", 2)
ADMIN = mock_user("admin", 3)


# ── App factory ───────────────────────────────────────────────────────────────

def _build_app() -> FastAPI:
    @asynccontextmanager
    async def _noop(app: FastAPI):
        yield

    app = FastAPI(lifespan=_noop)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    app.add_middleware(GZipMiddleware, minimum_size=500)
    setup_error_handlers(app)

    from routes import auth, dashboard, financial_records, health, users

    prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(financial_records.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    return app


# ── Base client (no user) ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Client with no authenticated user and a no-op DB session."""
    app = _build_app()
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: _yield(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Role-scoped clients ───────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def viewer_client():
    return await _client_for(VIEWER)


@pytest_asyncio.fixture
async def analyst_client():
    return await _client_for(ANALYST)


@pytest_asyncio.fixture
async def admin_client():
    return await _client_for(ADMIN)


async def _client_for(user: MagicMock):
    app = _build_app()
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: _yield(mock_db)
    app.dependency_overrides[get_current_user] = lambda: user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _yield(obj):
    yield obj
