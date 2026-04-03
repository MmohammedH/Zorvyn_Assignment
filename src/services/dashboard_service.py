from datetime import date, datetime
from calendar import month_abbr

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from enums.enums import RecordType
from log.logger import get_logger
from models.models import FinancialRecord, User
from schemas.dashboard_schemas import (
    CategoryBreakdownResponse,
    CategoryTotal,
    MonthlyTrend,
    RecentActivityResponse,
    RecentRecord,
    SummaryResponse,
    TrendResponse,
)

logger = get_logger(__name__)


_NOT_DELETED = FinancialRecord.is_deleted == False  # noqa: E712


async def get_summary(db: AsyncSession) -> SummaryResponse:
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME.value, FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.EXPENSE.value, FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_expenses"),
            func.count().label("total_records"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME.value, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("income_records"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.EXPENSE.value, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("expense_records"),
        )
        .where(_NOT_DELETED)
    )
    row = result.one()
    total_income = float(row.total_income)
    total_expenses = float(row.total_expenses)

    return SummaryResponse(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_balance=round(total_income - total_expenses, 2),
        total_records=row.total_records,
        income_records=row.income_records,
        expense_records=row.expense_records,
    )


async def get_category_breakdown(db: AsyncSession) -> CategoryBreakdownResponse:
    result = await db.execute(
        select(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count().label("count"),
        )
        .where(_NOT_DELETED)
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(FinancialRecord.type, func.sum(FinancialRecord.amount).desc())
    )
    rows = result.all()

    breakdown = [
        CategoryTotal(
            category=row.category,
            type=row.type,
            total=round(float(row.total), 2),
            count=row.count,
        )
        for row in rows
    ]
    return CategoryBreakdownResponse(breakdown=breakdown)


async def get_trends(db: AsyncSession, months: int = 6) -> TrendResponse:
    # Fetch all records and aggregate in Python for SQLite compatibility
    # (SQLite's strftime is available but less portable)
    result = await db.execute(
        select(
            FinancialRecord.record_date,
            FinancialRecord.type,
            FinancialRecord.amount,
        )
        .where(_NOT_DELETED)
        .order_by(FinancialRecord.record_date)
    )
    rows = result.all()

    # Determine month range: last `months` months from today
    today = date.today()
    month_map: dict[tuple[int, int], dict] = {}

    for m in range(months - 1, -1, -1):
        year = today.year
        month = today.month - m
        while month <= 0:
            month += 12
            year -= 1
        month_map[(year, month)] = {
            "year": year,
            "month": month,
            "total_income": 0.0,
            "total_expenses": 0.0,
        }

    for row in rows:
        key = (row.record_date.year, row.record_date.month)
        if key not in month_map:
            continue
        amount = float(row.amount)
        if row.type == RecordType.INCOME.value:
            month_map[key]["total_income"] += amount
        else:
            month_map[key]["total_expenses"] += amount

    trends = [
        MonthlyTrend(
            year=data["year"],
            month=data["month"],
            month_label=f"{data['year']}-{data['month']:02d}",
            total_income=round(data["total_income"], 2),
            total_expenses=round(data["total_expenses"], 2),
            net=round(data["total_income"] - data["total_expenses"], 2),
        )
        for data in month_map.values()
    ]
    return TrendResponse(months=trends, period_months=months)


async def get_recent_activity(db: AsyncSession, limit: int = 10) -> RecentActivityResponse:
    result = await db.execute(
        select(FinancialRecord)
        .options(selectinload(FinancialRecord.created_by))
        .where(_NOT_DELETED)
        .order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    recent = [
        RecentRecord(
            id=r.id,
            amount=float(r.amount),
            type=r.type,
            category=r.category,
            record_date=r.record_date.isoformat(),
            notes=r.notes,
            created_by_name=r.created_by.full_name if r.created_by else "Unknown",
        )
        for r in records
    ]
    return RecentActivityResponse(records=recent, total_shown=len(recent))
