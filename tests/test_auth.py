from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import VIEWER


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    fake_user = MagicMock(id=1, role="viewer")
    with patch("routes.auth.register_user", new=AsyncMock(return_value=(fake_user, "tok", 3600))):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "Secure@123", "full_name": "New User"},
        )
    assert resp.status_code == 201
    assert resp.json()["access_token"] == "tok"
    assert resp.json()["role"] == "viewer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    with patch("routes.auth.register_user", new=AsyncMock(side_effect=ValueError("already exists"))):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "Secure@123", "full_name": "Dup"},
        )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "u@test.com", "password": "weak", "full_name": "User"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "Secure@123", "full_name": "User"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={})
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    fake_user = MagicMock(id=1, role="viewer")
    with patch("routes.auth.authenticate_user", new=AsyncMock(return_value=(fake_user, "tok", 3600))):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "u@example.com", "password": "Secure@123"},
        )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_credentials(client: AsyncClient):
    with patch("routes.auth.authenticate_user", new=AsyncMock(side_effect=ValueError("bad creds"))):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "u@example.com", "password": "Wrong@123"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_account(client: AsyncClient):
    with patch(
        "routes.auth.authenticate_user",
        new=AsyncMock(side_effect=PermissionError("deactivated")),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "u@example.com", "password": "Secure@123"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={"email": "u@example.com"})
    assert resp.status_code == 422


# ── /users/me ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_returns_current_user(viewer_client):
    async with viewer_client as ac:
        resp = await ac.get("/api/v1/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "viewer@test.com"
    assert data["role"] == "viewer"
