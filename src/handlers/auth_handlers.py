from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from clients.db.connection import get_db
from enums.enums import UserRole
from log.logger import get_logger
from models.models import User
from services.user_service import get_user_by_id
from utils.security import decode_access_token

logger = get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as err:
        raise HTTPException(
            status_code=401,
            detail=str(err),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_id(db, int(user_id_str))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user


def require_role(*roles: UserRole):
    """Factory that returns a dependency enforcing one of the given roles."""

    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [r.value for r in roles]:
            allowed = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role(s): {allowed}",
            )
        return current_user

    return _checker


# Convenience dependencies
require_viewer = get_current_user  # Any authenticated user
require_analyst = require_role(UserRole.ANALYST, UserRole.ADMIN)
require_admin = require_role(UserRole.ADMIN)
