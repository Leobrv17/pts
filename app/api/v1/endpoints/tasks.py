"""Task API endpoints with cascade deletion."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile
from math import ceil

from app.api.deps import get_task_service, get_sprint_service, get_cascade_deletion_service
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, HttpResponseTaskList, TaskSpecifics, \
    TaskSpecificsResponse, HttpResponseTaskListResponse
from app.schemas.general_schemas import HttpResponseDeleteStatus
from app.services.task_service import TaskService
from app.services.cascade_deletion_service import CascadeDeletionService
from app.models.task import ImportCSVResponse, SourceType, EXPECTED_HEADERS, DB_FIELD_MAPPING
from app.services.sprint_service import SprintService
from app.utils.csv_import import validate_file_and_ids, parse_csv, validate_headers, \
    map_csv_to_tasks, build_response, process_tasks_and_duplicates, analyse_csv

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_task(
        taskData: TaskCreate,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Create a new task."""
    task = await task_service.create_task(taskData)
    return TaskResponse(
        id=str(task.id),
        sprintId=str(task.sprintId),
        projectId=str(task.projectId),
        key=task.key,
        summary=task.summary,
        storyPoints=task.storyPoints,
        wu=task.wu,
        comment=task.comment,
        deliverySprint=task.deliverySprint,
        deliveryVersion=task.deliveryVersion,
        type=task.type,
        status=task.status,
        rft=task.rft,
        technicalLoad=task.technicalLoad,
        timeSpent=task.timeSpent,
        timeRemaining=task.timeRemaining,
        progress=task.progress,
        assignee=[str(aid) for aid in task.assignee],
        delta=task.delta
    )


@router.get("/", response_model=HttpResponseTaskListResponse, response_model_by_alias=False)
async def get_tasks_by_ids(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Page size"),
        sprintIds: List[str] = Query(None, description="Filter by sprint ID"),
        isDeleted: Optional[bool] = Query(False, description="Filter by deleted task"),
        task_service: TaskService = Depends(get_task_service)
) -> HttpResponseTaskListResponse:
    """Get tasks with pagination and filters."""
    all_task_responses = []
    total = len(sprintIds)
    for sprint_id in sprintIds:
        tasks = await task_service.get_tasks_by_sprint(sprint_id, isDeleted)
        task_responses = [
            TaskResponse(
                id=str(task.id),
                sprintId=str(task.sprintId),
                projectId=str(task.projectId),
                key=task.key,
                summary=task.summary,
                storyPoints=task.storyPoints,
                wu=task.wu,
                comment=task.comment,
                deliverySprint=task.deliverySprint,
                deliveryVersion=task.deliveryVersion,
                type=task.type,
                status=task.status,
                rft=task.rft,
                technicalLoad=task.technicalLoad,
                timeSpent=task.timeSpent,
                timeRemaining=task.timeRemaining,
                progress=task.progress,
                assignee=[str(aid) for aid in task.assignee],
                delta=task.delta
            ) for task in tasks
        ]
        all_task_responses.append(HttpResponseTaskList(
            sprintId=sprint_id,
            taskList=task_responses,
        ))

    return HttpResponseTaskListResponse(
        responseList=all_task_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


@router.put("/update", response_model=TaskResponse, response_model_by_alias=False)
async def update_task(
        taskUpdate: TaskUpdate,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Update task."""
    task = await task_service.update_task(taskUpdate)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {taskUpdate.id} not found"
        )

    return TaskResponse(
        id=str(task.id),
        sprintId=str(task.sprintId),
        projectId=str(task.projectId),
        key=task.key,
        summary=task.summary,
        storyPoints=task.storyPoints,
        wu=task.wu,
        comment=task.comment,
        deliverySprint=task.deliverySprint,
        deliveryVersion=task.deliveryVersion,
        type=task.type,
        status=task.status,
        rft=task.rft,
        technicalLoad=task.technicalLoad,
        timeSpent=task.timeSpent,
        timeRemaining=task.timeRemaining,
        progress=task.progress,
        assignee=[str(aid) for aid in task.assignee],
        delta=task.delta
    )


@router.delete("/{taskId}", response_model=HttpResponseDeleteStatus, response_model_by_alias=False)
async def delete_task(
        taskId: str,
        cascade_deletion_service: CascadeDeletionService = Depends(get_cascade_deletion_service)
):
    """Delete task (soft delete) - individuelle uniquement."""
    success = await cascade_deletion_service.delete_task(taskId, is_cascade=False)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return HttpResponseDeleteStatus(
        status=success,
        msg=f"Task {taskId} deleted successfully." if success else f"Error during deletion of task {taskId}."
    )


@router.get("/types/", response_model=TaskSpecificsResponse, response_model_by_alias=False)
async def get_task_types(
        task_service: TaskService = Depends(get_task_service)
) -> TaskSpecificsResponse:
    """Get all existing task types and respective keys.
    For now only creates predefined list of types.
    Task Types should eventually be Database objects."""
    dummy_types = await task_service.get_task_type_list()

    type_list = [
        TaskSpecifics(
            key=key,
            specific=dummy_types[key]
        )
        for key in dummy_types
    ]
    return TaskSpecificsResponse(specifics=type_list)


@router.get("/statuses/", response_model=TaskSpecificsResponse, response_model_by_alias=False)
async def get_task_statuses(
        task_service: TaskService = Depends(get_task_service)
) -> TaskSpecificsResponse:
    """Get all existing task statuses and respective keys.
     For now only creates predefined list of statuses.
     Task Statuses should eventually be Database objects."""
    dummy_statuses = await task_service.get_task_status_list()

    status_list = [
        TaskSpecifics(
            key=key,
            specific=dummy_statuses[key]
        )
        for key in dummy_statuses
    ]
    return TaskSpecificsResponse(specifics=status_list)


@router.post("/import-csv", response_model=ImportCSVResponse, response_model_by_alias=False)
async def import_csv(
    projectId: str,
    sprintId: str,
    file: UploadFile,
    task_service: TaskService = Depends(get_task_service),
    sprint_service: SprintService = Depends(get_sprint_service)
) -> ImportCSVResponse:
    """Import tasks from a CSV file into a sprint within a project.

    Args:

        projectId (str): The ID of the project to import tasks into.
        sprintId (str): The ID of the sprint to import tasks into.
        file (UploadFile): The CSV file containing task data.
        source (SourceType): The source type of the CSV (e.g., JIRA or GITLAB).
        task_service (TaskService): The task service.
        sprint_service (SprintService): The sprint service.

    Returns:

        ImportCSVResponse: A response object detailing the import results, including counts and messages.

    Raises:

        HTTPException: If validation, parsing, or processing fails at any step.
    """
    sprintId, projectId = validate_file_and_ids(file, sprintId, projectId)
    sprint = await sprint_service.get_sprint_by_id(sprintId)
    content = await file.read()
    df, source_type = analyse_csv(content)
    mapped_df = map_csv_to_tasks(df, DB_FIELD_MAPPING[source_type], sprintId, projectId)
    tasks, total_count, duplicate_keys, invalid_rows = await process_tasks_and_duplicates(mapped_df, sprint,
                                                                                          task_service.engine)
    return build_response(tasks, duplicate_keys, invalid_rows)