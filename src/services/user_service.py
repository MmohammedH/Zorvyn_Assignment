from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enums.enums import UserRole
from log.logger import get_logger
from models.models import User
from schemas.user_schemas import CreateUserRequest, UpdateUserRequest
from utils.security import hash_password

logger = get_logger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_users(
    db: AsyncSession,
    role: str | None = None,
    is_active: bool | None = None,
) -> list[User]:
    query = select(User).order_by(User.created_at.desc())
    if role is not None:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_user(db: AsyncSession, request: CreateUserRequest) -> User:
    user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role=request.role.value,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("User created", extra={"user_id": user.id, "email": user.email, "role": user.role})
    return user


async def create_admin_seed(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("Admin seed user created", extra={"email": user.email})
    return user


async def update_user(db: AsyncSession, user: User, request: UpdateUserRequest) -> User:
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.role is not None:
        user.role = request.role.value
    if request.is_active is not None:
        user.is_active = request.is_active
    await db.flush()
    await db.refresh(user)
    logger.info(
        "User updated",
        extra={"user_id": user.id, "role": user.role, "is_active": user.is_active},
    )
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.flush()
    logger.info("User deleted", extra={"user_id": user.id})


async def user_count(db: AsyncSession) -> int:
    from sqlalchemy import func

    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar_one()
