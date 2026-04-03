from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import ADMIN, VIEWER


def _mock_record(**kwargs):
    r = MagicMock()
    r.id = kwargs.get("id", 1)
    r.created_by_id = kwargs.get("created_by_id", 3)
    r.amount = kwargs.get("amount", 100.0)
    r.type = kwargs.get("type", "income")
    r.category = kwargs.get("category", "salary")
    r.record_date = kwargs.get("record_date", date(2026, 1, 1))
    r.notes = kwargs.get("notes", None)
    r.is_deleted = False
    r.created_at = MagicMock()
    r.updated_at = MagicMock()
    return r


# ── Access control ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_records(client):
    resp = await client.get("/api/v1/records")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_viewer_cannot_create_record(viewer_client):
    async with viewer_client as ac:
        resp = await ac.post(
            "/api/v1/records",
            json={"amount": 500, "type": "income", "category": "salary", "record_date": "2026-01-01"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_update_record(viewer_client):
    async with viewer_client as ac:
        resp = await ac.put("/api/v1/records/1", json={"amount": 999})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_delete_record(viewer_client):
    async with viewer_client as ac:
        resp = await ac.delete("/api/v1/records/1")
    assert resp.status_code == 403


# ── Viewer reads ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_viewer_can_list_records(viewer_client):
    record = _mock_record()
    with patch("routes.financial_records.get_records", new=AsyncMock(return_value=([record], 1))):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/records")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["records"]) == 1


@pytest.mark.asyncio
async def test_viewer_can_get_single_record(viewer_client):
    record = _mock_record(id=5)
    with patch("routes.financial_records.get_record_by_id", new=AsyncMock(return_value=record)):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/records/5")
    assert resp.status_code == 200
    assert resp.json()["id"] == 5


@pytest.mark.asyncio
async def test_get_nonexistent_record_returns_404(viewer_client):
    with patch("routes.financial_records.get_record_by_id", new=AsyncMock(return_value=None)):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/records/999")
    assert resp.status_code == 404


# ── Admin CRUD ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_create_record(admin_client):
    record = _mock_record(amount=3000.0, type="income", category="salary")
    with patch("routes.financial_records.create_record", new=AsyncMock(return_value=record)):
        async with admin_client as ac:
            resp = await ac.post(
                "/api/v1/records",
                json={"amount": 3000, "type": "income", "category": "salary", "record_date": "2026-01-15"},
            )
    assert resp.status_code == 201
    assert resp.json()["amount"] == 3000.0


@pytest.mark.asyncio
async def test_admin_can_update_record(admin_client):
    existing = _mock_record(id=1, amount=100.0)
    updated = _mock_record(id=1, amount=250.0)
    with (
        patch("routes.financial_records.get_record_by_id", new=AsyncMock(return_value=existing)),
        patch("routes.financial_records.update_record", new=AsyncMock(return_value=updated)),
    ):
        async with admin_client as ac:
            resp = await ac.put("/api/v1/records/1", json={"amount": 250.0})
    assert resp.status_code == 200
    assert resp.json()["amount"] == 250.0


@pytest.mark.asyncio
async def test_admin_can_soft_delete_record(admin_client):
    record = _mock_record(id=1)
    with (
        patch("routes.financial_records.get_record_by_id", new=AsyncMock(return_value=record)),
        patch("routes.financial_records.soft_delete_record", new=AsyncMock(return_value=None)),
    ):
        async with admin_client as ac:
            resp = await ac.delete("/api/v1/records/1")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_record_returns_404(admin_client):
    with patch("routes.financial_records.get_record_by_id", new=AsyncMock(return_value=None)):
        async with admin_client as ac:
            resp = await ac.delete("/api/v1/records/999")
    assert resp.status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_negative_amount_rejected(admin_client):
    async with admin_client as ac:
        resp = await ac.post(
            "/api/v1/records",
            json={"amount": -100, "type": "income", "category": "salary", "record_date": "2026-01-01"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_category_for_type_rejected(admin_client):
    async with admin_client as ac:
        resp = await ac.post(
            "/api/v1/records",
            json={"amount": 100, "type": "income", "category": "food", "record_date": "2026-01-01"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_date_format_rejected(admin_client):
    async with admin_client as ac:
        resp = await ac.post(
            "/api/v1/records",
            json={"amount": 100, "type": "income", "category": "salary", "record_date": "not-a-date"},
        )
    assert resp.status_code == 422


# ── Filters ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_type(viewer_client):
    income = _mock_record(type="income")
    with patch("routes.financial_records.get_records", new=AsyncMock(return_value=([income], 1))):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/records?type=income")
    assert resp.status_code == 200
    assert resp.json()["records"][0]["type"] == "income"


@pytest.mark.asyncio
async def test_search_param_accepted(viewer_client):
    with patch("routes.financial_records.get_records", new=AsyncMock(return_value=([], 0))):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/records?search=salary")
    assert resp.status_code == 200
