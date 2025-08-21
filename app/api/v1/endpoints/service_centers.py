"""Service center API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil

from app.api.deps import get_project_service
from app.api.deps import get_service_center_service
from app.schemas.service_center import (
    ServiceCenterUpdate,
    ServiceCenterResponse,
    ServiceCenterListResponseLight,
    ServiceCenterLightResponse, ServiceCenterBase
)
from app.services.service_center_service import ServiceCenterService
from app.services.project_service import ProjectService
from app.schemas.project import ProjectLightResponse
from app.schemas.general_schemas import HttpResponseDeleteStatus

router = APIRouter()


@router.post("/", response_model=ServiceCenterResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_service_center(
    serviceCenterData: ServiceCenterBase,
    service_center_service: ServiceCenterService = Depends(get_service_center_service),
) -> ServiceCenterResponse:
    """Create a new service center."""
    service_center = await service_center_service.create_service_center(serviceCenterData)
    return ServiceCenterResponse(
        id=str(service_center.id),
        centerName=service_center.centerName,
        location=service_center.location,
        contactEmail=service_center.contactEmail,
        contactPhone=service_center.contactPhone,
        status=service_center.status,
        projects=[],
        users=[]
    )


@router.delete("/{serviceCenterId}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_service_center(
    serviceCenterId: str,
    service_center_service: ServiceCenterService = Depends(get_service_center_service)
):
    """Delete service center (soft delete)."""
    success = await service_center_service.delete_service_center(serviceCenterId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service center not found"
        )

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"Service center {serviceCenterId} deleted successfully." if success else f"Error during deletion of service center {serviceCenterId}."
    )


@router.get("/light", response_model=ServiceCenterListResponseLight, response_model_by_alias=False)
async def get_service_centers_light(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Page size"),
        isDeleted: Optional[bool] = Query(False, description="Filter by deleted center"),
        service_center_service: ServiceCenterService = Depends(get_service_center_service)
) -> ServiceCenterListResponseLight:
    """Get service centers in light format (only ID and name) with pagination."""
    skip = (page - 1) * size
    service_centers, total = await service_center_service.get_service_centers(
        skip=skip,
        limit=size,
        is_deleted=isDeleted
    )

    service_center_light_responses = [
        ServiceCenterLightResponse(
            _id=str(service_center.id),
            centerName=service_center.centerName
        )
        for service_center in service_centers
    ]

    return ServiceCenterListResponseLight(
        serviceCenters=service_center_light_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )

@router.get("/{serviceCenterId}", response_model=ServiceCenterResponse, response_model_by_alias=False)
async def get_service_center(
    serviceCenterId: str,
    isDeleted: bool = False,
    service_center_service: ServiceCenterService = Depends(get_service_center_service),
    project_service: ProjectService = Depends(get_project_service)
) -> ServiceCenterResponse:
    """Get service center by ID."""
    service_center = await service_center_service.get_service_center_by_id(serviceCenterId, isDeleted)
    if not service_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service center not found"
        )

    # users = await user_service.get_users_by_center(str(center.id))
    users = []  # Temporary. Should be added when User Roles are properly implemented.
    projects, _ = await project_service.get_projects(center_id=str(service_center.id), is_deleted=isDeleted)
    projects_light = []
    for project in projects:
        projects_light.append(
            ProjectLightResponse(
                id=str(project.id),
                centerId=str(project.centerId),
                projectName=project.projectName,
                status=project.status,
                sprints=[]
            )
        )

    return ServiceCenterResponse (
            id=str(service_center.id),
            centerName=service_center.centerName,
            location=service_center.location,
            contactEmail=service_center.contactEmail,
            contactPhone=service_center.contactPhone,
            status=service_center.status,
            projects=projects_light,
            users=users
        )


@router.put("/update", response_model=ServiceCenterResponse, response_model_by_alias=False)
async def update_service_center(
    serviceCenterUpdate: ServiceCenterUpdate,
    service_center_service: ServiceCenterService = Depends(get_service_center_service),
    project_service: ProjectService = Depends(get_project_service)
) -> ServiceCenterResponse:
    """Update service center."""
    service_center = await service_center_service.update_service_center(serviceCenterUpdate)
    if not service_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service center not found"
        )

    # users = await user_service.get_users_by_center(str(center.id))
    users = []  # Temporary. Should be added when User Roles are properly implemented.
    projects, _ = await project_service.get_projects(center_id=str(service_center.id))
    projects_light = []
    for project in projects:
        projects_light.append(
            ProjectLightResponse(
                id=str(project.id),
                centerId=str(project.centerId),
                projectName=project.projectName,
                status=project.status,
                sprints=[]
            )
        )

    return ServiceCenterResponse (
        id=str(service_center.id),
        centerName=service_center.centerName,
        location=service_center.location,
        contactEmail=service_center.contactEmail,
        contactPhone=service_center.contactPhone,
        status=service_center.status,
        projects=projects_light,
        users=users
    )
