from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from log.logger import get_logger
from models.models import FinancialRecord
from schemas.financial_record_schemas import (
    CreateFinancialRecordRequest,
    FinancialRecordFilterParams,
    UpdateFinancialRecordRequest,
)

logger = get_logger(__name__)


async def get_record_by_id(db: AsyncSession, record_id: int) -> FinancialRecord | None:
    result = await db.execute(
        select(FinancialRecord)
        .options(selectinload(FinancialRecord.created_by))
        .where(FinancialRecord.id == record_id, FinancialRecord.is_deleted == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def get_records(
    db: AsyncSession,
    filters: FinancialRecordFilterParams,
) -> tuple[list[FinancialRecord], int]:
    base_query = (
        select(FinancialRecord)
        .options(selectinload(FinancialRecord.created_by))
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
    )
    count_query = (
        select(func.count())
        .select_from(FinancialRecord)
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
    )

    conditions = _build_filter_conditions(filters)
    for condition in conditions:
        base_query = base_query.where(condition)
        count_query = count_query.where(condition)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.page_size
    base_query = (
        base_query.order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
        .offset(offset)
        .limit(filters.page_size)
    )
    result = await db.execute(base_query)
    records = list(result.scalars().all())

    return records, total


def _build_filter_conditions(filters: FinancialRecordFilterParams) -> list:
    conditions = []
    if filters.type is not None:
        conditions.append(FinancialRecord.type == filters.type.value)
    if filters.category is not None:
        conditions.append(FinancialRecord.category == filters.category.value)
    if filters.date_from is not None:
        conditions.append(FinancialRecord.record_date >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(FinancialRecord.record_date <= filters.date_to)
    if filters.search is not None:
        term = f"%{filters.search.strip()}%"
        conditions.append(
            or_(
                FinancialRecord.notes.ilike(term),
                FinancialRecord.category.ilike(term),
            )
        )
    return conditions


async def create_record(
    db: AsyncSession,
    request: CreateFinancialRecordRequest,
    created_by_id: int,
) -> FinancialRecord:
    record = FinancialRecord(
        created_by_id=created_by_id,
        amount=request.amount,
        type=request.type.value,
        category=request.category.value,
        record_date=request.record_date,
        notes=request.notes,
        is_deleted=False,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    logger.info(
        "Financial record created",
        extra={
            "record_id": record.id,
            "type": record.type,
            "amount": float(record.amount),
            "created_by_id": created_by_id,
        },
    )
    return record


async def update_record(
    db: AsyncSession,
    record: FinancialRecord,
    request: UpdateFinancialRecordRequest,
) -> FinancialRecord:
    if request.amount is not None:
        record.amount = request.amount
    if request.type is not None:
        record.type = request.type.value
    if request.category is not None:
        record.category = request.category.value
    if request.record_date is not None:
        record.record_date = request.record_date
    if request.notes is not None:
        record.notes = request.notes
    await db.flush()
    await db.refresh(record)
    logger.info("Financial record updated", extra={"record_id": record.id})
    return record


async def soft_delete_record(db: AsyncSession, record: FinancialRecord) -> None:
    record.is_deleted = True
    await db.flush()
    logger.info("Financial record soft-deleted", extra={"record_id": record.id})
