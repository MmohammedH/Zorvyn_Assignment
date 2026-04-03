from sqlalchemy.ext.asyncio import AsyncSession

from log.logger import get_logger
from models.models import User
from schemas.auth_schemas import LoginRequest, RegisterRequest
from schemas.user_schemas import CreateUserRequest
from services.user_service import create_user, get_user_by_email
from utils.security import create_access_token, verify_password
from enums.enums import UserRole

logger = get_logger(__name__)


async def authenticate_user(db: AsyncSession, request: LoginRequest) -> tuple[User, str, int]:
    user = await get_user_by_email(db, request.email)
    if not user:
        logger.warning("Login failed — email not found", extra={"email": request.email})
        raise ValueError("Invalid email or password")
    if not verify_password(request.password, user.hashed_password):
        logger.warning("Login failed — wrong password", extra={"user_id": user.id})
        raise ValueError("Invalid email or password")
    if not user.is_active:
        logger.warning("Login blocked — inactive user", extra={"user_id": user.id})
        raise PermissionError("Account is deactivated. Contact an administrator.")

    token, expires_in = create_access_token(user.id, user.role)
    logger.info("User logged in", extra={"user_id": user.id, "role": user.role})
    return user, token, expires_in


async def register_user(db: AsyncSession, request: RegisterRequest) -> tuple[User, str, int]:
    existing = await get_user_by_email(db, request.email)
    if existing:
        raise ValueError("An account with this email already exists")

    create_request = CreateUserRequest(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=UserRole.VIEWER,
    )
    user = await create_user(db, create_request)
    token, expires_in = create_access_token(user.id, user.role)
    logger.info("New user registered", extra={"user_id": user.id, "email": user.email})
    return user, token, expires_in
