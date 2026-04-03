from unittest.mock import AsyncMock, patch

import pytest

from schemas.dashboard_schemas import (
    CategoryBreakdownResponse,
    CategoryTotal,
    MonthlyTrend,
    RecentActivityResponse,
    RecentRecord,
    SummaryResponse,
    TrendResponse,
)


_SUMMARY = SummaryResponse(
    total_income=6000.0,
    total_expenses=1150.0,
    net_balance=4850.0,
    total_records=5,
    income_records=2,
    expense_records=3,
)

_BREAKDOWN = CategoryBreakdownResponse(
    breakdown=[
        CategoryTotal(category="salary", type="income", total=5000.0, count=1),
        CategoryTotal(category="food", type="expense", total=200.0, count=1),
    ]
)

_TRENDS = TrendResponse(
    months=[
        MonthlyTrend(year=2026, month=1, month_label="2026-01", total_income=5000, total_expenses=200, net=4800),
        MonthlyTrend(year=2026, month=2, month_label="2026-02", total_income=1000, total_expenses=150, net=850),
        MonthlyTrend(year=2026, month=3, month_label="2026-03", total_income=0, total_expenses=800, net=-800),
    ],
    period_months=3,
)

_RECENT = RecentActivityResponse(
    records=[
        RecentRecord(id=1, amount=500, type="income", category="salary", record_date="2026-03-01", notes=None, created_by_name="Admin"),
    ],
    total_shown=1,
)


# ── Summary ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summary_requires_auth(client):
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_summary_viewer_access(viewer_client):
    with patch("routes.dashboard.get_summary", new=AsyncMock(return_value=_SUMMARY)):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == 6000.0
    assert data["total_expenses"] == 1150.0
    assert data["net_balance"] == 4850.0


@pytest.mark.asyncio
async def test_summary_empty(viewer_client):
    empty = SummaryResponse(total_income=0, total_expenses=0, net_balance=0, total_records=0, income_records=0, expense_records=0)
    with patch("routes.dashboard.get_summary", new=AsyncMock(return_value=empty)):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["net_balance"] == 0.0


# ── Category breakdown ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_category_breakdown_requires_analyst(viewer_client):
    async with viewer_client as ac:
        resp = await ac.get("/api/v1/dashboard/by-category")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_category_breakdown_analyst_access(analyst_client):
    with patch("routes.dashboard.get_category_breakdown", new=AsyncMock(return_value=_BREAKDOWN)):
        async with analyst_client as ac:
            resp = await ac.get("/api/v1/dashboard/by-category")
    assert resp.status_code == 200
    assert len(resp.json()["breakdown"]) == 2


@pytest.mark.asyncio
async def test_category_breakdown_admin_access(admin_client):
    with patch("routes.dashboard.get_category_breakdown", new=AsyncMock(return_value=_BREAKDOWN)):
        async with admin_client as ac:
            resp = await ac.get("/api/v1/dashboard/by-category")
    assert resp.status_code == 200


# ── Trends ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trends_requires_analyst(viewer_client):
    async with viewer_client as ac:
        resp = await ac.get("/api/v1/dashboard/trends")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_trends_analyst_access(analyst_client):
    with patch("routes.dashboard.get_trends", new=AsyncMock(return_value=_TRENDS)):
        async with analyst_client as ac:
            resp = await ac.get("/api/v1/dashboard/trends?months=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["period_months"] == 3
    assert len(data["months"]) == 3


@pytest.mark.asyncio
async def test_trends_invalid_months(analyst_client):
    async with analyst_client as ac:
        resp = await ac.get("/api/v1/dashboard/trends?months=99")
    assert resp.status_code == 422


# ── Recent activity ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recent_requires_auth(client):
    resp = await client.get("/api/v1/dashboard/recent")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_recent_viewer_access(viewer_client):
    with patch("routes.dashboard.get_recent_activity", new=AsyncMock(return_value=_RECENT)):
        async with viewer_client as ac:
            resp = await ac.get("/api/v1/dashboard/recent")
    assert resp.status_code == 200
    assert resp.json()["total_shown"] == 1


@pytest.mark.asyncio
async def test_recent_limit_too_large(viewer_client):
    async with viewer_client as ac:
        resp = await ac.get("/api/v1/dashboard/recent?limit=999")
    assert resp.status_code == 422
