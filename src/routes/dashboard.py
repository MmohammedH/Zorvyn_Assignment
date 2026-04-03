from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clients.db.connection import get_db
from constants import ValidationConstants
from handlers.auth_handlers import get_current_user, require_analyst
from log.logger import get_logger
from models.models import User
from schemas.dashboard_schemas import (
    CategoryBreakdownResponse,
    RecentActivityResponse,
    SummaryResponse,
    TrendResponse,
)
from services.dashboard_service import (
    get_category_breakdown,
    get_recent_activity,
    get_summary,
    get_trends,
)
from utils.error_utils import handle_sqlalchemy_error

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Overall financial summary — totals and net balance [Viewer+]",
)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    try:
        return await get_summary(db)
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "fetching summary")


@router.get(
    "/by-category",
    response_model=CategoryBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Totals grouped by category and type [Analyst+]",
    dependencies=[Depends(require_analyst)],
)
async def category_breakdown(
    db: AsyncSession = Depends(get_db),
) -> CategoryBreakdownResponse:
    try:
        return await get_category_breakdown(db)
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "fetching category breakdown")


@router.get(
    "/trends",
    response_model=TrendResponse,
    status_code=status.HTTP_200_OK,
    summary="Monthly income vs expense trends [Analyst+]",
    dependencies=[Depends(require_analyst)],
)
async def trends(
    months: int = Query(
        default=ValidationConstants.DEFAULT_TREND_MONTHS,
        ge=1,
        le=24,
        description="Number of months to include (1–24)",
    ),
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    try:
        return await get_trends(db, months=months)
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "fetching trends")


@router.get(
    "/recent",
    response_model=RecentActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Most recent financial records [Viewer+]",
)
async def recent_activity(
    limit: int = Query(
        default=10,
        ge=1,
        le=ValidationConstants.MAX_RECENT_RECORDS,
        description="Number of recent records to return",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecentActivityResponse:
    try:
        return await get_recent_activity(db, limit=limit)
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "fetching recent activity")
