"""Project API endpoints with cascade deletion from service centers."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil

from app.api.v1.endpoints.sprints import get_sprints_light
from app.api.deps import get_sprint_service, get_task_service, get_cascade_deletion_service
from app.api.deps import get_project_service
from app.schemas.project import (
    ProjectUpdate, ProjectResponse, ProjectTransversalActivityResponse,
    ProjectListResponseLight, ProjectBase, ProjectCreate, ProjectLightResponse, ProjectTransversalActivityCreate
)
from app.services.project_service import ProjectService
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService
from app.services.cascade_deletion_service import CascadeDeletionService
from app.schemas.sprint import SprintLightResponse
from app.schemas.general_schemas import HttpResponseDeleteStatus
from app.utils.calculations import calculate_sprint_metrics
from app.models.project import ProjectTransversalActivity

router = APIRouter()


async def build_trans_act_response(project_id: str, project_service: ProjectService = Depends(get_project_service)) \
        -> List[ProjectTransversalActivityResponse]:
    """Build basic ProjectTransversalActivity response."""
    trans_acts = await project_service.get_project_transversal_activities_by_project(project_id)
    trans_acts_response = []
    for ta in trans_acts:
        trans_acts_response.append(
            ProjectTransversalActivityResponse(
                _id=str(ta.id),
                name=ta.activity,
                description=ta.meaning
            )
        )

    return trans_acts_response


async def build_sprint_light_response(project_id: str,
                                      sprint_service: SprintService = Depends(get_sprint_service),
                                      task_service: TaskService = Depends(get_task_service)) \
    -> List[SprintLightResponse]:
    """Build basic SprintLight response."""
    sprints, _ = await sprint_service.get_sprints(project_id=project_id)
    sprints_response = []
    for s in sprints:
        s_tas = await sprint_service.get_sprint_transversal_activities_by_sprint(str(s.id))
        s_tasks = await task_service.get_tasks_by_sprint(str(s.id))
        sprint_metrics = await calculate_sprint_metrics(s, s_tas, s_tasks)
        sprints_response.append(
            SprintLightResponse(
                id=str(s.id),
                projectId=str(s.projectId),
                sprintName=s.sprintName,
                status=s.status,
                startDate=s.startDate,
                dueDate=s.dueDate,
                scoped=sprint_metrics["scoped"],
                capacity=s.capacity,
                velocity=sprint_metrics["velocity"],
                progress=sprint_metrics["progress"],
                timeSpent=sprint_metrics["time_spent"],
                otd=sprint_metrics["otd"],
                oqd=sprint_metrics["oqd"]
            )
        )

    return sprints_response


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_project(
        projectData: ProjectCreate,
        project_service: ProjectService = Depends(get_project_service),
        task_service: TaskService = Depends(get_task_service)
) -> ProjectResponse:
    """Create a new project."""
    task_statuses = await task_service.get_task_status_list()
    task_statuses = [sid for sid, sv in task_statuses.items()]
    task_types = await task_service.get_task_type_list()
    task_types = [tid for tid, tv in task_types.items()]
    project_full_data = ProjectBase(
        centerId=projectData.centerId,
        projectName=projectData.projectName,
        status=projectData.status,
        technicalLoadRatio=1.0,
        taskStatuses=task_statuses,
        taskTypes=task_types
    )

    project = await project_service.create_project(project_full_data)
    await project_service.create_default_transversal_activities(str(project.id))

    trans_acts_response = await build_trans_act_response(str(project.id), project_service)

    return ProjectResponse(
        _id=str(project.id),
        projectName=project.projectName,
        status=project.status,
        centerId=str(project.centerId) if project.centerId else None,
        sprints=[],
        users=[],
        technicalLoadRatio=project.transversal_vs_technical_workload_ratio,
        transversalActivities=trans_acts_response,
        taskStatuses=task_statuses,
        taskTypes=task_types
    )


@router.get("/light", response_model=ProjectListResponseLight, response_model_by_alias=False)
async def get_projects_light(
        centerId: str = None,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Page size"),
        isDeleted: Optional[bool] = Query(False, description="Filter by deleted projects"),
        project_service: ProjectService = Depends(get_project_service),
        sprint_service: SprintService = Depends(get_sprint_service),
        task_service: TaskService = Depends(get_task_service)
) -> ProjectListResponseLight:
    """Get service centers in light format (only ID and name) with pagination."""
    skip = (page - 1) * size
    projects, total = await project_service.get_projects(
        skip=skip,
        limit=size,
        center_id=centerId,
        is_deleted=isDeleted
    )

    project_light_responses = []

    for project in projects:
        sprint_responses = await get_sprints_light(
            project_id=str(project.id),
            sprint_service=sprint_service,
            task_service=task_service,
            isDeleted=isDeleted
        )

        project_light_responses.append(
            ProjectLightResponse(
                id=str(project.id),
                centerId=str(project.centerId),
                projectName=project.projectName,
                status=project.status,
                sprints=sprint_responses.sprints
            )
        )

    return ProjectListResponseLight(
        projects=project_light_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


@router.put("/update", response_model=ProjectResponse, response_model_by_alias=False)
async def update_project(
        projectUpdate: ProjectUpdate,
        project_service: ProjectService = Depends(get_project_service),
        sprint_service: SprintService = Depends(get_sprint_service),
        task_service: TaskService = Depends(get_task_service)
) -> ProjectResponse:
    """Update project."""
    task_statuses = await task_service.get_task_status_list()
    task_types = await task_service.get_task_type_list()
    if projectUpdate.taskTypes:
        projectUpdate.taskTypes = [ttid for ttid,_ in task_types.items() if ttid in projectUpdate.taskTypes]
    if projectUpdate.taskStatuses:
        projectUpdate.taskStatuses = [tsid for tsid,_ in task_statuses.items() if tsid in projectUpdate.taskStatuses]

    project = await project_service.update_project(projectUpdate)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {projectUpdate.id} not found"
        )

    if projectUpdate.transversalActivities:
        p_tas = await project_service.get_project_transversal_activities_by_project(str(project.id))
        old_ptas_ids = [str(ta.id) for ta in p_tas]
        new_ptas_ids = [ta.id for ta in projectUpdate.transversalActivities if ta.id]
        for ta in projectUpdate.transversalActivities:
            if ta.id and ta.id in old_ptas_ids:
                # Update old ProjectTA if new id is present in old list
                await project_service.update_project_transversal_activity(ProjectTransversalActivity(
                    id=ta.id,
                    project_id=project.id,
                    activity=ta.name,
                    meaning=ta.description
                ))
            else:
                # Create new ProjectTA if new id is not present in old list (or new TA does not have an id)
                await project_service.create_project_transversal_activity(ProjectTransversalActivityCreate(
                    projectId=str(project.id),
                    activity=ta.name if ta.name else "Activity",
                    meaning=ta.description if ta.description else ""
                ))

        # Delete old ProjectTA if old id is not present in the new list
        for old_ta_id in old_ptas_ids:
            if old_ta_id not in new_ptas_ids:
                await project_service.delete_project_transversal_activity(old_ta_id)

    sprints_response = await build_sprint_light_response(str(project.id), sprint_service, task_service)
    trans_acts_response = await build_trans_act_response(str(project.id), project_service)

    return ProjectResponse(
        _id=str(project.id),
        projectName=project.projectName,
        status=project.status,
        centerId=str(project.centerId) if project.centerId else None,
        sprints=sprints_response,
        users=[],
        taskTypes=project.task_types,
        taskStatuses=project.task_statuses,
        technicalLoadRatio=project.transversal_vs_technical_workload_ratio,
        transversalActivities=trans_acts_response
    )


@router.delete("/{projectId}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_project(
        projectId: str,
        cascade_deletion_service: CascadeDeletionService = Depends(get_cascade_deletion_service)
):
    """Delete project with cascade deletion (soft delete) - individuelle uniquement."""
    success = await cascade_deletion_service.delete_project_with_cascade(projectId, is_cascade=False)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"Project {projectId} and all related elements deleted successfully (cascade)" if success else f"Error during cascade deletion of project {projectId}."
    )


@router.get("/{projectId}/cascade-deleted", response_model=dict, response_model_by_alias=False)
async def get_cascade_deleted_elements(
        projectId: str,
        cascade_deletion_service: CascadeDeletionService = Depends(get_cascade_deletion_service)
):
    """Get all elements that were cascade deleted from this project."""
    return await cascade_deletion_service.get_cascade_deleted_elements("project", projectId)


@router.get("/byIds/", response_model=List[ProjectResponse], response_model_by_alias=False)
async def get_projects_by_ids(
        projectIds: List[str] = Query(..., description="List of project IDs to retrieve"),
        isDeleted: Optional[bool] = Query(False, description="Filter by deleted projects"),
        project_service: ProjectService = Depends(get_project_service),
        sprint_service: SprintService = Depends(get_sprint_service),
        task_service: TaskService = Depends(get_task_service)
) -> List[ProjectResponse]:
    """Get projects by a list of IDs."""
    project_responses = []

    for pid in projectIds:
        project = await project_service.get_project_by_id(pid, isDeleted)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {pid} not found"
            )
        task_statuses = project.task_statuses if project.task_statuses else []
        task_types = project.task_types if project.task_types else []

        sprints_response = await build_sprint_light_response(pid, sprint_service, task_service)
        trans_acts_response = await build_trans_act_response(pid, project_service)

        project_responses.append(
            ProjectResponse(
                _id=str(project.id),
                projectName=project.projectName,
                status=project.status,
                centerId=str(project.centerId) if project.centerId else None,
                sprints=sprints_response,
                users=[],
                taskTypes=task_types,
                taskStatuses=task_statuses,
                technicalLoadRatio=project.transversal_vs_technical_workload_ratio,
                transversalActivities=trans_acts_response
            )
        )

    return project_responses