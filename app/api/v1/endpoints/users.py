"""User API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil

from app.api.deps import get_user_service
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    DirectorAccessCreate, DirectorAccessUpdate, DirectorAccessResponse,
    ProjectAccessCreate, ProjectAccessUpdate, ProjectAccessResponse,
    UserByNameRequest, UserByNameResponse
)
from app.schemas.general_schemas import HttpResponseDeleteStatus
from app.services.user_service import UserService

router = APIRouter()


async def build_user_response(user, user_service: UserService) -> UserResponse:
    """Build a complete user response with access lists."""
    # Get director access list
    director_accesses = await user_service.get_director_access_by_user(str(user.id))
    director_access_responses = [
        DirectorAccessResponse(
            id=str(da.id),
            service_center_id=str(da.service_center_id),
            service_center_name=da.service_center_name
        )
        for da in director_accesses
    ]

    # Get project access list
    project_accesses = await user_service.get_project_access_by_user(str(user.id))
    project_access_responses = [
        ProjectAccessResponse(
            id=str(pa.id),
            service_center_id=str(pa.service_center_id),
            service_center_name=pa.service_center_name,
            project_id=str(pa.project_id),
            project_name=pa.project_name,
            access_level=pa.access_level,
            occupancy_rate=pa.occupancy_rate
        )
        for pa in project_accesses
    ]

    return UserResponse(
        _id=str(user.id),
        first_name=user.first_name,
        family_name=user.family_name,
        email=user.email,
        type=user.type,
        registration_number=user.registration_number,
        trigram=user.trigram,
        director_access_list=director_access_responses,
        project_access_list=project_access_responses
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_user(
        user_data: UserCreate,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create a new user."""
    user = await user_service.create_user(user_data)
    return await build_user_response(user, user_service)


@router.get("/", response_model=UserListResponse, response_model_by_alias=False)
async def get_users(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Page size"),
        nameSubstring: Optional[str] = Query(None, description="Filter by name substring"),
        isDeleted: Optional[bool] = Query(False, description="Filter by deleted user"),
        user_service: UserService = Depends(get_user_service)
) -> UserListResponse:
    """Get users with pagination and filters."""
    skip = (page - 1) * size
    users, total = await user_service.get_users(
        skip=skip,
        limit=size,
        name_substring=nameSubstring,
        is_deleted=isDeleted
    )

    user_responses = []
    for user in users:
        user_response = await build_user_response(user, user_service)
        user_responses.append(user_response)

    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


@router.get("/search", response_model=UserByNameResponse, response_model_by_alias=False)
async def get_users_by_name(
        name: Optional[str] = Query(None, description="Name fragment to search for"),
        isDeleted: Optional[bool] = Query(False, description="Include deleted users"),
        user_service: UserService = Depends(get_user_service)
) -> UserByNameResponse:
    """Get users by name substring."""
    users = await user_service.get_users_by_name(
        name_substring=name,
        is_deleted=isDeleted,
        limit=10
    )

    user_responses = []
    for user in users:
        user_response = await build_user_response(user, user_service)
        user_responses.append(user_response)

    return UserByNameResponse(users=user_responses)


@router.get("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
async def get_user(
        user_id: str,
        isDeleted: bool = Query(False, description="Include deleted user"),
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Get user by ID."""
    user = await user_service.get_user_by_id(user_id, isDeleted)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return await build_user_response(user, user_service)


@router.put("/{user_id}", response_model=UserResponse, response_model_by_alias=False)
async def update_user(
        user_id: str,
        user_update: UserUpdate,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Update user."""
    user = await user_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return await build_user_response(user, user_service)


@router.delete("/{user_id}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_user(
        user_id: str,
        user_service: UserService = Depends(get_user_service)
) -> HttpResponseDeleteStatus:
    """Delete user (soft delete)."""
    success = await user_service.delete_user(user_id)

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"User {user_id} deleted successfully" if success else f"Error during deletion of user {user_id}"
    )
