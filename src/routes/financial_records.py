from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clients.db.connection import get_db
from enums.enums import RecordCategory, RecordType
from handlers.auth_handlers import get_current_user, require_admin
from log.logger import get_logger
from models.models import User
from schemas.financial_record_schemas import (
    CreateFinancialRecordRequest,
    FinancialRecordFilterParams,
    FinancialRecordListResponse,
    FinancialRecordResponse,
    UpdateFinancialRecordRequest,
)
from services.financial_record_service import (
    create_record,
    get_record_by_id,
    get_records,
    soft_delete_record,
    update_record,
)
from utils.error_utils import handle_sqlalchemy_error

logger = get_logger(__name__)

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.get(
    "",
    response_model=FinancialRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="List financial records with optional filters [Viewer+]",
)
async def list_records(
    type: RecordType | None = Query(None, description="Filter by record type"),
    category: RecordCategory | None = Query(None, description="Filter by category"),
    date_from: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    search: str | None = Query(None, max_length=100, description="Search in notes or category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialRecordListResponse:
    try:
        filters = FinancialRecordFilterParams(
            type=type,
            category=category,
            date_from=date_from,
            date_to=date_to,
            search=search,
            page=page,
            page_size=page_size,
        )
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    try:
        records, total = await get_records(db, filters)
        return FinancialRecordListResponse(
            records=[FinancialRecordResponse.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "listing records")


@router.post(
    "",
    response_model=FinancialRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a financial record [Admin]",
)
async def create_financial_record(
    request: CreateFinancialRecordRequest = Body(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> FinancialRecordResponse:
    try:
        record = await create_record(db, request, created_by_id=current_user.id)
        return FinancialRecordResponse.model_validate(record)
    except IntegrityError as err:
        from utils.error_utils import handle_integrity_error

        handle_integrity_error(err, "creating record")
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "creating record")


@router.get(
    "/{record_id}",
    response_model=FinancialRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single financial record [Viewer+]",
)
async def get_financial_record(
    record_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialRecordResponse:
    try:
        record = await get_record_by_id(db, record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial record {record_id} not found",
            )
        return FinancialRecordResponse.model_validate(record)
    except HTTPException:
        raise
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "fetching record")


@router.put(
    "/{record_id}",
    response_model=FinancialRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a financial record [Admin]",
)
async def update_financial_record(
    record_id: int = Path(..., ge=1),
    request: UpdateFinancialRecordRequest = Body(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> FinancialRecordResponse:
    try:
        record = await get_record_by_id(db, record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial record {record_id} not found",
            )
        updated = await update_record(db, record, request)
        return FinancialRecordResponse.model_validate(updated)
    except HTTPException:
        raise
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "updating record")


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a financial record [Admin]",
)
async def delete_financial_record(
    record_id: int = Path(..., ge=1),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        record = await get_record_by_id(db, record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial record {record_id} not found",
            )
        await soft_delete_record(db, record)
    except HTTPException:
        raise
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "deleting record")
