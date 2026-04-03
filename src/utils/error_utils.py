from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from log.logger import get_logger

logger = get_logger(__name__)


def handle_integrity_error(err: IntegrityError, operation: str) -> None:
    logger.warning(f"IntegrityError during {operation}", extra={"error": str(err.orig)})
    detail = "A record with the provided data already exists."
    if err.orig and "UNIQUE" in str(err.orig).upper():
        detail = "A record with this unique value already exists."
    raise HTTPException(status_code=409, detail=detail)


def handle_sqlalchemy_error(err: SQLAlchemyError, operation: str) -> None:
    logger.error(f"SQLAlchemyError during {operation}: {err}")
    raise HTTPException(
        status_code=503,
        detail="Database service temporarily unavailable. Please try again.",
    )


def handle_unexpected_error(err: Exception, operation: str) -> None:
    logger.exception(f"Unexpected error during {operation}", extra={"error": str(err)})
    raise HTTPException(
        status_code=500,
        detail="An unexpected error occurred. Please try again later.",
    )
