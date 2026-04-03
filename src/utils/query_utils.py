from fastapi import HTTPException

from constants import ValidationConstants


def validate_query_string(
    value: str | None,
    field_name: str,
    max_length: int = ValidationConstants.QUERY_STRING_MAX_LENGTH,
) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty if provided")
    if len(stripped) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} cannot exceed {max_length} characters",
        )
    return stripped
