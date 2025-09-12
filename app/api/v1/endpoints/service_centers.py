"""Service center API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil

from app.api.deps import get_project_service, get_cascade_deletion_service, get_user_service
from app.api.deps import get_service_center_service
from app.schemas.service_center import (
    ServiceCenterUpdate,
    ServiceCenterResponse,
    ServiceCenterListResponseLight,
    ServiceCenterLightResponse, ServiceCenterBase
)
from app.schemas.user import UserBase
from app.services.service_center_service import ServiceCenterService
from app.services.project_service import ProjectService
from app.services.user_service import UserService
from app.services.cascade_deletion_service import CascadeDeletionService
from app.schemas.project import ProjectLightResponse
from app.schemas.general_schemas import HttpResponseDeleteStatus
from app.schemas.user import UserBase, UserServiceCenterResponse, UserProjectSummary
from typing import List

router = APIRouter()


async def build_user_base_response(user) -> UserBase:
    """Build a UserBase response for service center."""
    return UserBase(
        id=str(user.id),
        firstName=user.first_name,
        familyName=user.family_name,
        email=user.email,
        type=user.type,
        registrationNumber=user.registration_number,
        trigram=user.trigram
    )


async def build_users_list_for_service_center(center_id: str, user_service: UserService) -> list[UserBase]:
    """Build users list for a service center based on director and project access."""
    # Récupérer tous les utilisateurs qui ont des accès directeur ou projet sur ce centre
    director_accesses = await user_service.get_director_accesses_by_service_center(center_id)
    project_accesses = await user_service.get_project_accesses_by_service_center(center_id)

    # Rassembler tous les user_ids uniques
    user_ids = set()
    for da in director_accesses:
        user_ids.add(str(da.user_id))
    for pa in project_accesses:
        user_ids.add(str(pa.user_id))

    if not user_ids:
        return []

    # Récupérer les utilisateurs
    users = await user_service.get_users_by_ids(list(user_ids))

    # Construire les réponses UserBase
    user_responses = []
    for user in users:
        user_response = await build_user_base_response(user)
        user_responses.append(user_response)

    return user_responses


async def build_users_list_for_service_center_detailed(center_id: str, user_service: UserService) -> List[
    UserServiceCenterResponse]:
    """Build detailed users list for a service center with projects and occupancy aggregation."""
    # Récupérer tous les utilisateurs qui ont des accès directeur ou projet sur ce centre
    director_accesses = await user_service.get_director_accesses_by_service_center(center_id)
    project_accesses = await user_service.get_project_accesses_by_service_center(center_id)

    # Organiser les données par utilisateur
    user_data = {}

    # Traiter les accès directeur
    for da in director_accesses:
        user_id = str(da.user_id)
        if user_id not in user_data:
            user_data[user_id] = {
                'is_director': True,
                'projects': []
            }
        else:
            user_data[user_id]['is_director'] = True

    # Traiter les accès projet
    for pa in project_accesses:
        user_id = str(pa.user_id)
        if user_id not in user_data:
            user_data[user_id] = {
                'is_director': False,
                'projects': []
            }

        # Ajouter le projet à la liste
        user_data[user_id]['projects'].append({
            'id': str(pa.project_id),
            'projectName': pa.project_name,
            'accessLevel': pa.access_level,
            'occupancyRate': pa.occupancy_rate
        })

    if not user_data:
        return []

    # Récupérer les utilisateurs complets
    user_ids = list(user_data.keys())
    users = await user_service.get_users_by_ids(user_ids)

    # Construire les réponses détaillées
    user_responses = []
    for user in users:
        user_id = str(user.id)
        user_info = user_data.get(user_id, {'is_director': False, 'projects': []})

        # Créer les objets UserProjectSummary
        project_summaries = [
            UserProjectSummary(
                id=proj['id'],
                projectName=proj['projectName'],
                accessLevel=proj['accessLevel'],
                occupancyRate=proj['occupancyRate']
            )
            for proj in user_info['projects']
        ]

        # Calculer l'occupancy total
        total_occupancy = sum(proj['occupancyRate'] for proj in user_info['projects'])

        user_response = UserServiceCenterResponse(
            id=str(user.id),
            firstName=user.first_name,
            familyName=user.family_name,
            projects=project_summaries,
            totalOccupancyRate=total_occupancy
        )
        user_responses.append(user_response)

    return user_responses


@router.post("/", response_model=ServiceCenterResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_service_center(
    serviceCenterData: ServiceCenterBase,
    service_center_service: ServiceCenterService = Depends(get_service_center_service),
    user_service: UserService = Depends(get_user_service)
) -> ServiceCenterResponse:
    """Create a new service center."""
    service_center = await service_center_service.create_service_center(serviceCenterData)

    # Récupérer les utilisateurs associés à ce centre
    users = await build_users_list_for_service_center(str(service_center.id), user_service)

    return ServiceCenterResponse(
        id=str(service_center.id),
        centerName=service_center.centerName,
        location=service_center.location,
        contactEmail=service_center.contactEmail,
        contactPhone=service_center.contactPhone,
        status=service_center.status,
        projects=[],
        users=users
    )


@router.delete("/{serviceCenterId}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_service_center(
    serviceCenterId: str,
    cascade_deletion_service: CascadeDeletionService = Depends(get_cascade_deletion_service)
):
    """Delete service center with cascade deletion (soft delete)."""
    success = await cascade_deletion_service.delete_service_center_with_cascade(serviceCenterId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service center not found"
        )

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"Service center {serviceCenterId} and all related elements deleted successfully (cascade)" if success else f"Error during cascade deletion of service center {serviceCenterId}."
    )


# @router.get("/{serviceCenterId}/cascade-deleted", response_model=dict, response_model_by_alias=False)
# async def get_cascade_deleted_elements(
#         serviceCenterId: str,
#         cascade_deletion_service: CascadeDeletionService = Depends(get_cascade_deletion_service)
# ):
#     """Get all elements that were cascade deleted from this service center."""
#     return await cascade_deletion_service.get_cascade_deleted_elements("service_center", serviceCenterId)


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
        project_service: ProjectService = Depends(get_project_service),
        user_service: UserService = Depends(get_user_service)
) -> ServiceCenterResponse:
    """Get service center by ID."""
    service_center = await service_center_service.get_service_center_by_id(serviceCenterId, isDeleted)
    if not service_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service center not found"
        )

    # Récupérer les utilisateurs avec leurs projets et occupancy détaillés
    users = await build_users_list_for_service_center_detailed(serviceCenterId, user_service)

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

    return ServiceCenterResponse(
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
    project_service: ProjectService = Depends(get_project_service),
    user_service: UserService = Depends(get_user_service)
) -> ServiceCenterResponse:
    """Update service center."""
    service_center = await service_center_service.update_service_center(serviceCenterUpdate)
    if not service_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service center not found"
        )

    # Récupérer les utilisateurs associés à ce centre
    users = await build_users_list_for_service_center(str(service_center.id), user_service)

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