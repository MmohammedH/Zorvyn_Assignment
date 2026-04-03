import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from constants import ValidationConstants
from enums.enums import UserRole


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class CreateUserRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=ValidationConstants.PASSWORD_MIN_LENGTH,
        max_length=ValidationConstants.PASSWORD_MAX_LENGTH,
    )
    full_name: str = Field(
        ...,
        min_length=ValidationConstants.FULL_NAME_MIN_LENGTH,
        max_length=ValidationConstants.FULL_NAME_MAX_LENGTH,
    )
    role: UserRole = Field(default=UserRole.VIEWER)

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Email is required")
        email = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email format")
        return email

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Full name is required")
        return v.strip()


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(
        None,
        min_length=ValidationConstants.FULL_NAME_MIN_LENGTH,
        max_length=ValidationConstants.FULL_NAME_MAX_LENGTH,
    )
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: Any) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()
