"""
Admin-only routes -- user provisioning, password resets, and the
user list. Every route here requires require_admin (superadmin only).
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.auth.dependencies import require_admin
from app.schemas.admin import (
    CreateUserRequest,
    CreateUserResponse,
    ResetUserPasswordRequest,
    ResetUserPasswordResponse,
    UserListResponse,
)
from app.schemas.auth import CurrentUser
from app.services.admin_service import (
    UserNotFoundError,
    UsernameAlreadyExistsError,
    create_member,
    list_members,
    reset_member_password,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: CreateUserRequest,
    current_user: CurrentUser = Depends(require_admin),
) -> CreateUserResponse:
    try:
        return await create_member(payload.username, payload.password)
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Username already exists", "code": "USERNAME_ALREADY_EXISTS"},
        )


@router.patch("/users/{username}/password", response_model=ResetUserPasswordResponse)
async def reset_user_password_route(
    payload: ResetUserPasswordRequest,
    username: str = Path(..., min_length=3, max_length=50),
    current_user: CurrentUser = Depends(require_admin),
) -> ResetUserPasswordResponse:
    try:
        return await reset_member_password(username, payload.new_password)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "code": "USER_NOT_FOUND"},
        )


@router.get("/users", response_model=UserListResponse)
async def list_users_route(
    current_user: CurrentUser = Depends(require_admin),
) -> UserListResponse:
    return await list_members()