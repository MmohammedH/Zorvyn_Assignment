from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from constants import ValidationConstants
from enums.enums import RecordCategory, RecordType


class FinancialRecordResponse(BaseModel):
    id: int
    created_by_id: int
    amount: float
    type: str
    category: str
    record_date: date
    notes: str | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FinancialRecordListResponse(BaseModel):
    records: list[FinancialRecordResponse]
    total: int
    page: int
    page_size: int


class CreateFinancialRecordRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": 2500.00,
                "type": "income",
                "category": "salary",
                "record_date": "2026-04-01",
                "notes": "Monthly salary",
            }
        }
    }

    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    type: RecordType = Field(..., description="income or expense")
    category: RecordCategory = Field(..., description="Record category")
    record_date: date = Field(..., description="Date of the transaction (YYYY-MM-DD)")
    notes: str | None = Field(
        None,
        max_length=ValidationConstants.NOTES_MAX_LENGTH,
        description="Optional description or notes",
    )

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Any) -> float:
        try:
            value = float(v)
        except (TypeError, ValueError):
            raise ValueError("Amount must be a number")
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        # Round to 2 decimal places
        return round(value, 2)

    @field_validator("record_date", mode="before")
    @classmethod
    def validate_record_date(cls, v: Any) -> date:
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        raise ValueError("Invalid date")

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, v: Any) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("Notes must be a string")
        stripped = v.strip()
        return stripped if stripped else None

    @model_validator(mode="after")
    def validate_category_matches_type(self) -> "CreateFinancialRecordRequest":
        income_categories = {
            RecordCategory.SALARY,
            RecordCategory.INVESTMENT,
            RecordCategory.FREELANCE,
            RecordCategory.BONUS,
            RecordCategory.OTHER,
        }
        expense_categories = {
            RecordCategory.FOOD,
            RecordCategory.TRANSPORT,
            RecordCategory.ENTERTAINMENT,
            RecordCategory.UTILITIES,
            RecordCategory.HEALTHCARE,
            RecordCategory.EDUCATION,
            RecordCategory.HOUSING,
            RecordCategory.SHOPPING,
            RecordCategory.OTHER,
        }
        if self.type == RecordType.INCOME and self.category not in income_categories:
            raise ValueError(
                f"Category '{self.category.value}' is not valid for income records. "
                f"Valid categories: {[c.value for c in income_categories]}"
            )
        if self.type == RecordType.EXPENSE and self.category not in expense_categories:
            raise ValueError(
                f"Category '{self.category.value}' is not valid for expense records. "
                f"Valid categories: {[c.value for c in expense_categories]}"
            )
        return self


class UpdateFinancialRecordRequest(BaseModel):
    amount: float | None = Field(None, gt=0)
    type: RecordType | None = None
    category: RecordCategory | None = None
    record_date: date | None = None
    notes: str | None = Field(None, max_length=ValidationConstants.NOTES_MAX_LENGTH)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            value = float(v)
        except (TypeError, ValueError):
            raise ValueError("Amount must be a number")
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(value, 2)

    @field_validator("record_date", mode="before")
    @classmethod
    def validate_record_date(cls, v: Any) -> date | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        raise ValueError("Invalid date")

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, v: Any) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("Notes must be a string")
        stripped = v.strip()
        return stripped if stripped else None


class FinancialRecordFilterParams(BaseModel):
    type: RecordType | None = None
    category: RecordCategory | None = None
    date_from: date | None = None
    date_to: date | None = None
    search: str | None = Field(None, max_length=100, description="Search in notes and category")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self) -> "FinancialRecordFilterParams":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")
        return self
