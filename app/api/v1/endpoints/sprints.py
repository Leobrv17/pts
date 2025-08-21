"""Sprint API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from math import ceil

from app.api.deps import get_sprint_service, get_task_service, get_project_service
from app.schemas.sprint import (
    SprintCreate, SprintUpdate, SprintResponse, SprintListResponse,
    SprintTransversalActivityUpdate, SprintTransversalActivityResponse,
    SprintListResponseLight, SprintLightResponse
)
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService
from app.utils.calculations import calculate_sprint_metrics
from app.schemas.task import TaskResponse
from app.services.project_service import ProjectService
from app.models.sprint import SprintTransversalActivity
from app.schemas.general_schemas import HttpResponseDeleteStatus

router = APIRouter()


async def build_trans_act_response(sprint_id: str, sprint_service: SprintService) -> List[SprintTransversalActivityResponse]:
    """Build basic SprintTA response."""
    s_tas = await sprint_service.get_sprint_transversal_activities_by_sprint(sprint_id)
    trans_acts_response = []
    for ta in s_tas:
        trans_acts_response.append(
            SprintTransversalActivityResponse(
                id=str(ta.id),
                name=ta.activity,
                description=ta.meaning,
                timeSpent=ta.time_spent
            )
        )

    return trans_acts_response


async def build_task_response(sprint_id: str, task_service: TaskService) -> List[TaskResponse]:
    """Build basic task response."""
    s_tasks = await task_service.get_tasks_by_sprint(sprint_id)
    task_response = []
    for task in s_tasks:
        assignees = [str(ass) for ass in task.assignee]
        task_response.append(TaskResponse(
            id=str(task.id),
            sprintId=str(task.sprintId),
            projectId=str(task.projectId),
            type=task.type,
            key=task.key,
            summary=task.summary,
            storyPoints=task.storyPoints,
            wu=task.wu,
            status=task.status,
            progress=task.progress,
            comment=task.comment,
            deliverySprint=task.deliverySprint,
            deliveryVersion=task.deliveryVersion,
            rft=task.rft,
            assignee=assignees,
            technicalLoad=task.technicalLoad,
            timeSpent=task.timeSpent,
            timeRemaining=task.timeRemaining,
            delta=task.delta
        ))

    return task_response


@router.post("/", response_model=SprintResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_sprint(
    sprintData: SprintCreate,
    sprint_service: SprintService = Depends(get_sprint_service),
    project_service: ProjectService = Depends(get_project_service)
) -> SprintResponse:
    """Create a new sprint."""
    sprint = await sprint_service.create_sprint(sprintData)
    trans_acts = await project_service.get_project_transversal_activities_by_project(sprintData.projectId)
    ta_response = []
    for ta in trans_acts:
        act = await sprint_service.create_sprint_transversal_activity(
            SprintTransversalActivity(
                sprintId=sprint.id,
                activity=ta.activity,
                meaning=ta.meaning
            )
        )
        ta_response.append(SprintTransversalActivityResponse(
            id=str(act.id),
            name=act.activity,
            description=act.meaning,
            timeSpent=0.0,
        ))

    s_tas = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sprint.id))
    relevant_sprint_response = await sprint_service.get_relevant_sprints_by_project(str(sprint.projectId))
    sprint_metrics = await calculate_sprint_metrics(sprint, s_tas, [])

    return SprintResponse(
        id=str(sprint.id),
        projectId=str(sprint.projectId),
        capacity=sprint.capacity,
        sprintName=sprint.sprintName,
        status=sprint.status,
        startDate=sprint.startDate,
        dueDate=sprint.dueDate,
        duration=sprint_metrics["duration"],
        scoped=sprint_metrics["scoped"],
        velocity=sprint_metrics["velocity"],
        progress=sprint_metrics["progress"],
        timeSpent=sprint_metrics["time_spent"],
        otd=sprint_metrics["otd"],
        oqd=sprint_metrics["oqd"],
        tasks=[],
        sprintTargets=relevant_sprint_response,
        transversalActivities=ta_response
    )


@router.get("/", response_model=SprintListResponse, response_model_by_alias=False)
async def get_sprints(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    sprintIds: List[str] = Query(None, description="Filter by sprint IDs"),
    projectId: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    isDeleted: Optional[bool] = Query(False, description="Filter by deleted sprint"),
    sprint_service: SprintService = Depends(get_sprint_service),
    task_service: TaskService = Depends(get_task_service),
    project_service: ProjectService = Depends(get_project_service)
) -> SprintListResponse:
    """Get sprints with pagination and filters."""
    skip = (page - 1) * size
    sprints, total = await sprint_service.get_sprints(
        skip=skip,
        limit=size,
        sprint_ids=sprintIds,
        project_id=projectId,
        status=status,
        is_deleted=isDeleted
    )

    sprint_responses = []
    for sprint in sprints:
        s_tasks = await task_service.get_tasks_by_sprint(str(sprint.id), isDeleted)
        s_tas = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sprint.id), isDeleted)
        sprint_metrics = await calculate_sprint_metrics(sprint, s_tas, s_tasks)

        task_response = await build_task_response(str(sprint.id), task_service)
        trans_acts_response = await build_trans_act_response(str(sprint.id), sprint_service)
        relevant_sprint_response = await sprint_service.get_relevant_sprints_by_project(str(sprint.projectId))

        task_statuses = []
        task_types = []
        try:
            project = await project_service.get_project_by_id(str(sprint.projectId), isDeleted)
            if project:
                task_statuses = project.task_statuses if project.task_statuses else []
                task_types = project.task_types if project.task_types else []
        except Exception:
            pass

        sprint_responses.append(SprintResponse(
            id=str(sprint.id),
            projectId=str(sprint.projectId),
            capacity=sprint.capacity,
            sprintName=sprint.sprintName,
            status=sprint.status,
            startDate=sprint.startDate,
            dueDate=sprint.dueDate,
            duration=sprint_metrics["duration"],
            tasks=task_response,
            scoped=sprint_metrics["scoped"],
            velocity=sprint_metrics["velocity"],
            progress=sprint_metrics["progress"],
            timeSpent=sprint_metrics["time_spent"],
            otd=sprint_metrics["otd"],
            oqd=sprint_metrics["oqd"],
            sprintTargets=relevant_sprint_response,
            transversalActivities=trans_acts_response,
            taskStatuses=task_statuses,
            taskTypes=task_types
        ))

    return SprintListResponse(
        sprints=sprint_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


async def get_sprints_light(
        project_id: str,
        isDeleted: bool = False,
        sprint_service: SprintService = Depends(get_sprint_service),
        task_service: TaskService = Depends(get_task_service)
) -> SprintListResponseLight:
    """Get service centers in light format (only ID and name) with pagination."""
    sprints, _ = await sprint_service.get_sprints(project_id=project_id, is_deleted=isDeleted)

    sprint_responses = []
    for sprint in sprints:
        trans_acts = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sprint.id), isDeleted)
        tasks = await task_service.get_tasks_by_sprint(str(sprint.id), isDeleted)
        sprint_metrics = await calculate_sprint_metrics(sprint, trans_acts, tasks)
        sprint_responses.append(
            SprintLightResponse(
                id=str(sprint.id),
                projectId=str(sprint.projectId),
                sprintName=sprint.sprintName,
                status=sprint.status,
                startDate=sprint.startDate,
                dueDate=sprint.dueDate,
                scoped=sprint_metrics["scoped"],
                capacity=sprint.capacity,
                velocity=sprint_metrics["velocity"],
                progress=sprint_metrics["progress"],
                timeSpent=sprint_metrics["time_spent"],
                otd=sprint_metrics["otd"],
                oqd=sprint_metrics["oqd"]
            )
        )

    return SprintListResponseLight(sprints=sprint_responses)


@router.put("/update", response_model=SprintResponse, response_model_by_alias=False)
async def update_sprint(
    sprintUpdate: SprintUpdate,
    sprint_service: SprintService = Depends(get_sprint_service),
    task_service: TaskService = Depends(get_task_service)
) -> SprintResponse:
    """Update sprint."""
    sprint = await sprint_service.update_sprint(sprintUpdate)
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found"
        )

    s_tas = await sprint_service.get_sprint_transversal_activities_by_sprint(sprintUpdate.id)
    s_tasks = await task_service.get_tasks_by_sprint(sprintUpdate.id)
    sprint_metrics = await calculate_sprint_metrics(sprint, s_tas, s_tasks)

    if sprintUpdate.transversalActivities:
        old_stas_ids = [str(ta.id) for ta in s_tas]
        new_stas_ids = [ta.id for ta in sprintUpdate.transversalActivities if ta.id]
        for ta in sprintUpdate.transversalActivities:
            if ta.id and ta.id in old_stas_ids:
                # Update old SprintTA if new id is present in old list
                await sprint_service.update_sprint_transversal_activity(SprintTransversalActivityUpdate(
                    id=ta.id,
                    name=ta.name,
                    description=ta.description,
                    timeSpent=ta.timeSpent
                ))
            else:
                # Create new SprintTA if new id is not present in old list (or new TA does not have an id)
                await sprint_service.create_sprint_transversal_activity(SprintTransversalActivity(
                    sprintId=sprint.id,
                    activity=ta.name if ta.name else "",
                    meaning=ta.description if ta.description else "",
                    time_spent=ta.timeSpent if ta.timeSpent else 0
                ))

        # Delete old SprintTA if old id is not present in the new list
        for old_ta_id in old_stas_ids:
            if old_ta_id not in new_stas_ids:
                await sprint_service.delete_sprint_transversal_activity(old_ta_id)

    trans_acts_response = await build_trans_act_response(str(sprint.id), sprint_service)
    task_response = await build_task_response(str(sprint.id), task_service)
    relevant_sprint_response = await sprint_service.get_relevant_sprints_by_project(str(sprint.projectId))

    return SprintResponse(
        id=str(sprint.id),
        projectId=str(sprint.projectId),
        sprintName=sprint.sprintName,
        status=sprint.status,
        startDate=sprint.startDate,
        dueDate=sprint.dueDate,
        capacity=sprint.capacity,
        duration=sprint_metrics["duration"],
        scoped=sprint_metrics["scoped"],
        velocity=sprint_metrics["velocity"],
        progress=sprint_metrics["progress"],
        timeSpent=sprint_metrics["time_spent"],
        otd=sprint_metrics["otd"],
        oqd=sprint_metrics["oqd"],
        tasks=task_response,
        sprintTargets=relevant_sprint_response,
        transversalActivities=trans_acts_response
    )


@router.delete("/{sprintId}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_sprint(
    sprintId: str,
    sprint_service: SprintService = Depends(get_sprint_service)
):
    """Delete sprint (soft delete)."""
    success = await sprint_service.delete_sprint(sprintId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found"
        )

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"Sprint {sprintId} deleted successfully." if success else f"Error during deletion of sprint {sprintId}."
    )