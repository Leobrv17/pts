from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from bson import ObjectId
from fastapi import UploadFile, HTTPException

from app.api.v1.endpoints.tasks import import_csv
from app.models.project import Project
from app.models.sprint import Sprint, SprintStatus
from app.models.task import SourceType, ImportCSVResponse, Task, TaskType, TaskStatus
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.insert_one = AsyncMock()
    return engine


@pytest.fixture
def mock_async_engine():
    return AsyncMock()


@pytest.fixture
def valid_object_id():
    return ObjectId()

@pytest.fixture
def mock_csv_file():
    file = MagicMock(spec=UploadFile)
    file.filename = "test.csv"
    file.read = AsyncMock(return_value=b'Issue key,Issue Type,Summary,Custom field (Story Points)\nTASK-1,Task,Test Task,3.0\n')
    return file


@pytest.fixture
def mock_sprint(valid_object_id):
    """Create a mock Sprint with all required fields."""
    now = datetime.now(ZoneInfo("UTC"))
    return Sprint(
        id=valid_object_id,
        projectId=valid_object_id,
        sprintName="Test Sprint",
        status=SprintStatus.TODO,
        startDate=now,
        dueDate=now + timedelta(days=14),
        capacity=40.0,
        task=[],
        is_deleted=False
    )


@pytest.mark.asyncio
async def test_import_csv_success(mock_engine, mock_async_engine, valid_object_id, mock_csv_file, mock_sprint):
    """Test successful CSV import with valid data."""
    mock_async_engine.find_one = AsyncMock(side_effect=[mock_sprint, MagicMock(Project)])

    mock_async_engine.find = AsyncMock(return_value=[])
    mock_async_engine.save_all = AsyncMock()
    mock_async_engine.save = AsyncMock()
    mock_async_engine.count = AsyncMock(return_value=1)

    mock_engine.find_one_return_value = mock_sprint
    sprint_service = SprintService(mock_engine)
    task_service = TaskService(mock_async_engine)

    response = await import_csv(
        projectId=str(valid_object_id),
        sprintId=str(valid_object_id),
        file=mock_csv_file,
        source=SourceType.JIRA,
        sprint_service=sprint_service,
        task_service=task_service
    )

    assert isinstance(response, ImportCSVResponse)
    assert "Successfully imported" in response.msg


@pytest.mark.asyncio
async def test_import_csv_invalid_file_extension(mock_engine, mock_async_engine, valid_object_id):
    """Test CSV import with invalid file extension."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test.txt"

    sprint_service = SprintService(mock_engine)
    task_service = TaskService(mock_async_engine)

    with pytest.raises(HTTPException) as exc_info:
        await import_csv(
            projectId=str(valid_object_id),
            sprintId=str(valid_object_id),
            file=file,
            source=SourceType.JIRA,
            sprint_service=sprint_service,
            task_service=task_service
        )

    assert exc_info.value.status_code == 400
    assert "Only CSV files are allowed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_csv_invalid_sprint(mock_engine, mock_async_engine, valid_object_id, mock_csv_file):
    """Test CSV import with invalid sprint ID."""
    mock_async_engine.find_one = AsyncMock(return_value=None)
    mock_engine.find_one.return_value = None
    sprint_service = SprintService(mock_engine)
    task_service = TaskService(mock_async_engine)

    with pytest.raises(HTTPException) as exc_info:
        await import_csv(
            projectId=str(valid_object_id),
            sprintId=str(valid_object_id),
            file=mock_csv_file,
            source=SourceType.JIRA,
            sprint_service=sprint_service,
            task_service=task_service
        )

    assert exc_info.value.status_code == 404
    assert "Sprint" in exc_info.value.detail
    assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_csv_with_duplicates(mock_engine, mock_async_engine, valid_object_id, mock_sprint):
    """Test CSV import with duplicate tasks."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test.csv"
    file.read = AsyncMock(
        return_value=b'Issue key,Issue Type,Summary,Custom field (Story Points)\nTASK-1,Task,Test Task,3.0\nTASK-1,Task,Duplicate Task,5.0\n')

    mock_async_engine.find_one = AsyncMock(side_effect=[mock_sprint, MagicMock(Project)])

    existing_task = Task(
        key="TASK-1",
        summary="Existing Task",
        type=TaskType.TASK,
        status=TaskStatus.TODO,
        sprintId=valid_object_id,
        projectId=valid_object_id
    )
    mock_async_engine.find = AsyncMock(return_value=[existing_task])
    mock_async_engine.count = AsyncMock(return_value=1)
    task_service = TaskService(mock_async_engine)
    mock_engine.find_one.return_value = mock_sprint
    sprint_service = SprintService(mock_engine)

    response = await import_csv(
        projectId=str(valid_object_id),
        sprintId=str(valid_object_id),
        file=file,
        source=SourceType.JIRA,
        task_service=task_service,
        sprint_service=sprint_service
    )

    assert "tasks were not added because they already exist" in response.msg


@pytest.mark.asyncio
async def test_import_csv_with_invalid_rows(mock_engine, mock_async_engine, valid_object_id, mock_sprint):
    """Test CSV import with invalid row data."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test.csv"
    file.read = AsyncMock(
        return_value=b'Issue key,Issue Type,Summary,Custom field (Story Points)\nTASK-1,Task\nTASK-2,Task,Valid Task\n')

    mock_async_engine.find_one = AsyncMock(side_effect=[mock_sprint, MagicMock(Project)])
    mock_async_engine.find = AsyncMock(return_value=[])
    mock_async_engine.count = AsyncMock(return_value=1)
    task_service = TaskService(mock_async_engine)
    sprint_service = SprintService(mock_engine)

    response = await import_csv(
        projectId=str(valid_object_id),
        sprintId=str(valid_object_id),
        file=file,
        source=SourceType.JIRA,
        sprint_service=sprint_service,
        task_service=task_service
    )
    assert response.msg == "Successfully imported 1 tasks"
