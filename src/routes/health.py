from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
async def health_check() -> JSONResponse:
    settings = get_settings()
    return JSONResponse(
        content={
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }
    )
