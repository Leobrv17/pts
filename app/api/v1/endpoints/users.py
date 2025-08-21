"""User API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil

from app.api.deps import get_user_service
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_user(
        user_data: UserCreate,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create a new user."""
    user = await user_service.create_user(user_data)
    return UserResponse(
        _id=str(user.id),
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        status=user.status,
        trigram=user.trigram,
    )


@router.get("/", response_model=UserListResponse, response_model_by_alias=False)
async def get_users(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Page size"),
        role: Optional[str] = Query(None, description="Filter by role"),
        status: Optional[str] = Query(None, description="Filter by status"),
        nameSubstring: Optional[str] = Query(None, description="Filter by name"),
        isDeleted: Optional[bool] = Query(False, description="Filter by deleted user"),
        user_service: UserService = Depends(get_user_service)
) -> UserListResponse:
    """Get users with pagination and filters."""
    skip = (page - 1) * size
    users, total = await user_service.get_users(
        skip=skip,
        limit=size,
        role=role,
        status=status,
        name_substring=nameSubstring,
        is_deleted=isDeleted
    )

    user_responses = [
        UserResponse(
            _id=str(user.id),
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            status=user.status,
            trigram=user.trigram,
        )
        for user in users
    ]

    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


@router.get("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
async def get_user(
        user_id: str,
        isDeleted: bool = False,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Get user by ID."""
    user = await user_service.get_user_by_id(user_id, isDeleted)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        _id=str(user.id),
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        status=user.status,
        trigram=user.trigram,
    )


@router.put("/update", response_model=UserResponse, response_model_by_alias=False)
async def update_user(
        user_id: str,
        userUpdate: UserUpdate,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Update user."""
    user = await user_service.update_user(user_id, userUpdate)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        _id=str(user.id),
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        status=user.status,
        trigram=user.trigram,
    )


@router.delete("/{userId}", status_code=status.HTTP_204_NO_CONTENT, response_model_by_alias=False)
async def delete_user(
        userId: str,
        user_service: UserService = Depends(get_user_service)
):
    """Delete user (soft delete)."""
    success = await user_service.delete_user(userId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/project/{project_id}", response_model=List[UserResponse], response_model_by_alias=False)
async def get_users_by_project(
        project_id: str,
        isDeleted: bool = False,
        user_service: UserService = Depends(get_user_service)
) -> List[UserResponse]:
    """Get users by project ID."""
    users = await user_service.get_users_by_project(project_id, isDeleted)

    return [
        UserResponse(
            _id=str(user.id),
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            status=user.status,
            trigram=user.trigram,
        )
        for user in users
    ]