from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clients.db.connection import get_db
from log.logger import get_logger
from middleware.rate_limiter import limiter
from schemas.auth_schemas import LoginRequest, RegisterRequest, TokenResponse
from services.auth_service import authenticate_user, register_user
from utils.error_utils import handle_integrity_error, handle_sqlalchemy_error

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (defaults to Viewer role)",
)
@limiter.limit("20/minute")
async def register(
    request: Request,
    body: RegisterRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        user, token, expires_in = await register_user(db, body)
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user_id=user.id,
            role=user.role,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except IntegrityError as err:
        handle_integrity_error(err, "registering user")
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "registering user")


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive a JWT access token",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        user, token, expires_in = await authenticate_user(db, body)
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user_id=user.id,
            role=user.role,
        )
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except ValueError:
        # Intentionally vague — do not reveal whether email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "logging in")
