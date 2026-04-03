from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from clients.db.connection import get_db
from handlers.auth_handlers import get_current_user, require_admin
from log.logger import get_logger
from models.models import User
from schemas.user_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from services.user_service import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_id,
    update_user,
)
from utils.error_utils import handle_integrity_error, handle_sqlalchemy_error

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users [Admin]",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    try:
        users = await get_all_users(db, role=role, is_active=is_active)
        responses = [UserResponse.model_validate(u) for u in users]
        return UserListResponse(users=responses, total=len(responses))
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "listing users")


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user [Admin]",
    dependencies=[Depends(require_admin)],
)
async def create_new_user(
    request: CreateUserRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        user = await create_user(db, request)
        return UserResponse.model_validate(user)
    except IntegrityError as err:
        handle_integrity_error(err, "creating user")
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "creating user")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user by ID [Admin or self]",
)
async def get_user(
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    from enums.enums import UserRole

    # Users can view their own profile; admins can view anyone's
    if current_user.role != UserRole.ADMIN.value and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "fetching user")


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user [Admin]",
    dependencies=[Depends(require_admin)],
)
async def update_existing_user(
    user_id: int = Path(..., ge=1),
    request: UpdateUserRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        updated = await update_user(db, user, request)
        return UserResponse.model_validate(updated)
    except HTTPException:
        raise
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "updating user")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user [Admin]",
    dependencies=[Depends(require_admin)],
)
async def delete_existing_user(
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        await delete_user(db, user)
    except HTTPException:
        raise
    except IntegrityError as err:
        handle_integrity_error(err, "deleting user")
    except SQLAlchemyError as err:
        handle_sqlalchemy_error(err, "deleting user")
