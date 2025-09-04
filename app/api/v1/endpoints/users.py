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
            serviceCenterId=str(da.service_center_id),
            serviceCenterName=da.service_center_name
        )
        for da in director_accesses
    ]

    # Get project access list
    project_accesses = await user_service.get_project_access_by_user(str(user.id))
    project_access_responses = [
        ProjectAccessResponse(
            id=str(pa.id),
            serviceCenterId=str(pa.service_center_id),
            serviceCenterName=pa.service_center_name,
            projectId=str(pa.project_id),
            projectName=pa.project_name,
            accessLevel=pa.access_level,
            occupancyRate=pa.occupancy_rate
        )
        for pa in project_accesses
    ]

    return UserResponse(
        id=str(user.id),
        firstName=user.first_name,
        familyName=user.family_name,
        email=user.email,
        type=user.type,
        registrationNumber=user.registration_number,
        trigram=user.trigram,
        directorAccessList=director_access_responses,
        projectAccessList=project_access_responses
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_user(
        userData: UserCreate,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create a new user."""
    user = await user_service.create_user(userData)
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


@router.get("/byIds/", response_model=List[UserResponse], response_model_by_alias=False)
async def get_users_by_ids(
        userIds: List[str] = Query(..., description="List of user IDs to retrieve"),
        isDeleted: Optional[bool] = Query(False, description="Include deleted users"),
        user_service: UserService = Depends(get_user_service)
) -> List[UserResponse]:
    """Get users by a list of IDs."""
    # Récupérer tous les utilisateurs d'un coup pour optimiser
    users = await user_service.get_users_by_ids(userIds, isDeleted)

    # Vérifier que tous les utilisateurs demandés ont été trouvés
    found_user_ids = {str(user.id) for user in users}
    missing_user_ids = set(userIds) - found_user_ids

    if missing_user_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Users not found: {', '.join(missing_user_ids)}"
        )

    # Construire les réponses
    user_responses = []
    for user in users:
        user_response = await build_user_response(user, user_service)
        user_responses.append(user_response)

    return user_responses





@router.put("/{userId}", response_model=UserResponse, response_model_by_alias=False)
async def update_user(
        userId: str,
        userUpdate: UserUpdate,
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Update user."""
    user = await user_service.update_user(userId, userUpdate)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return await build_user_response(user, user_service)


@router.delete("/{userId}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_user(
        userId: str,
        user_service: UserService = Depends(get_user_service)
) -> HttpResponseDeleteStatus:
    """Delete user (soft delete)."""
    success = await user_service.delete_user(userId)

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"User {userId} deleted successfully" if success else f"Error during deletion of user {userId}"
    )