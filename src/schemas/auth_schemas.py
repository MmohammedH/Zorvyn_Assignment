import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from constants import ValidationConstants


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Email is required")
        return v.strip().lower()

    @field_validator("password", mode="before")
    @classmethod
    def validate_password_present(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Password is required")
        return v


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=ValidationConstants.PASSWORD_MIN_LENGTH,
        max_length=ValidationConstants.PASSWORD_MAX_LENGTH,
        description="Password (min 8 chars, must include uppercase, lowercase, digit, special char)",
    )
    full_name: str = Field(
        ...,
        min_length=ValidationConstants.FULL_NAME_MIN_LENGTH,
        max_length=ValidationConstants.FULL_NAME_MAX_LENGTH,
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Email is required")
        email = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email format")
        return email

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Full name is required")
        return v.strip()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user_id: int
    role: str
