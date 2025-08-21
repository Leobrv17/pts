from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.models.task import TASKRFT, TaskType, TaskStatus, Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.insert_one = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_create_task(mock_engine):
    """Test POST api/tasks/ service-side"""
    task_create = TaskCreate(
        sprintId=str(ObjectId()),
        projectId=str(ObjectId()),
        type="Bug",
        key="Test Task",
        summary="A task to test task creation",
        status="In progress"
    )

    mock_engine.save.return_value = None
    task_service = TaskService(mock_engine)
    task = await task_service.create_task(task_create)

    excepted_result = Task(
        id=task.id,     # Would always be different
        sprintId=task_create.sprintId,
        projectId=task_create.projectId,
        key=task_create.key,
        summary=task_create.summary,
        storyPoints=0,
        wu="",
        comment="",
        deliverySprint="",
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=[],
        delta=0,
        created_at=task.created_at  # Would always be different (by a few milliseconds)
    )

    assert task == excepted_result


@pytest.mark.asyncio
async def test_get_task_by_id_not_found(mock_engine):
    """Test get_task_by_id exception"""
    mock_engine.find_one.return_value = None
    task_service = TaskService(mock_engine)

    with pytest.raises(HTTPException):
        await task_service.get_task_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_update_task(mock_engine):
    """Test PUT /api/tasks/ service-side"""
    task = Task(
        id=ObjectId(),
        sprintId=ObjectId(),
        projectId=ObjectId(),
        key="Example Task",
        summary="Example summary",
        storyPoints=0,
        wu="Example wu",
        comment="Example comment",
        deliverySprint="",
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=[],
        delta=0,
    )

    task_update = TaskUpdate(
        id=str(task.id),
        sprintId=str(ObjectId()),
        projectId=str(ObjectId()),
        summary="New summary",
        storyPoints=10,
        deliverySprint=str(ObjectId()),
        assignee=[str(ObjectId())]
    )

    mock_engine.save.return_value = None
    mock_engine.find_one.return_value = task
    task_service = TaskService(mock_engine)
    updated_task = await task_service.update_task(task_update)

    expected_result = Task(
        id=task.id,
        sprintId=ObjectId(task_update.sprintId),
        projectId=ObjectId(task_update.projectId),
        key="Example Task",
        summary="New summary",
        storyPoints=10,
        wu="Example wu",
        comment="Example comment",
        deliverySprint=updated_task.deliverySprint,
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=task_update.assignee,
        delta=0,
        created_at = task.created_at
    )

    assert updated_task == expected_result


@pytest.mark.asyncio
async def test_update_task_not_found(mock_engine):
    """Test PUT api/tasks/ with task not found"""
    task_update = TaskUpdate(
        id=str(ObjectId()),
        projectId=str(ObjectId()),
        summary="New summary",
        storyPoints=10,
        assignee=[str(ObjectId())]
    )

    mock_engine.save.return_value = None
    mock_engine.find_one.return_value = None
    task_service = TaskService(mock_engine)
    with pytest.raises(HTTPException):
        await task_service.update_task(task_update)


@pytest.mark.asyncio
async def test_delete_task(mock_engine):
    """Test DELETE api/tasks/{taskId} service-side"""
    task = Task(
        id=ObjectId(),
        sprintId=ObjectId(),
        projectId=ObjectId(),
        key="Example Task",
        summary="Example summary",
        storyPoints=0,
        wu="Example wu",
        comment="Example comment",
        deliverySprint="",
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=[],
        delta=0,
        is_deleted=False
    )

    mock_engine.find_one.return_value = task
    mock_engine.save.return_value = task
    task_service = TaskService(mock_engine)
    is_task_deleted = await task_service.delete_task(str(task.id))

    assert is_task_deleted
    assert task.is_deleted


@pytest.mark.asyncio
async def test_delete_task_not_found(mock_engine):
    """Test DELETE api/tasks/{taskId} with task not found"""
    mock_engine.find_one.return_value = None
    task_service = TaskService(mock_engine)
    with pytest.raises(HTTPException):
        await task_service.delete_task(str(ObjectId()))


@pytest.mark.asyncio
async def test_get_task_by_sprint(mock_engine):
    """Test GET api/tasks/ service-side"""
    target_sprint = ObjectId()
    task1 = Task(
        id=ObjectId(),
        sprintId=target_sprint,
        projectId=ObjectId(),
        key="Example Task",
        summary="Example summary",
        storyPoints=0,
        wu="Example wu",
        comment="Example comment",
        deliverySprint="",
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=[],
        delta=0
    )
    task2 = Task(
        id=ObjectId(),
        sprintId=target_sprint,
        projectId=task1.projectId,
        key="Example Task",
        summary="Example summary",
        storyPoints=0,
        wu="Example wu",
        comment="Example comment",
        deliverySprint="",
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=[],
        delta=0,
        is_deleted=False
    )
    task3 = Task(
        id=ObjectId(),
        sprintId=ObjectId(),
        projectId=task1.projectId,
        key="Example Task",
        summary="Example summary",
        storyPoints=0,
        wu="Example wu",
        comment="Example comment",
        deliverySprint="",
        deliveryVersion="",
        type=TaskType.BUG,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.DEFAULT,
        technicalLoad=0,
        timeSpent=0,
        timeRemaining=0,
        progress=0,
        assignee=[],
        delta=0,
        is_deleted=False
    )
    tasks = [task1, task2, task3]

    mock_engine.find.return_value = [t for t in tasks if t.sprintId == target_sprint]
    task_service = TaskService(mock_engine)
    tasks_by_sprint = await task_service.get_tasks_by_sprint(str(target_sprint))

    assert tasks_by_sprint == [task1, task2]


@pytest.mark.asyncio
async def test_get_task_types(mock_engine):
    """Test GET api/tasks/types service-side"""
    expected_result = {
        "BUG": "Bug",
        "TASK": "Task",
        "STORY": "Story",
        "EPIC": "Epic",
        "DOC": "Doc",
        "TEST": "Test",
        "DELIVERABLE": "Deliverable"
    }

    task_service = TaskService(mock_engine)
    assert await task_service.get_task_type_list() == expected_result


@pytest.mark.asyncio
async def test_get_task_statuses(mock_engine):
    """Test /api/tasks/statuses service-side"""
    expected_result = {
        "OPEN": "Open",
        "TODO": "To do",
        "INVEST": "Under investigation",
        "PROG": "In progress",
        "REV": "In review",
        "CUST": "Waiting for customer",
        "STANDBY": "Standby",
        "DONE": "Done",
        "CANCEL": "Cancelled",
        "POST": "Postponed"
    }

    task_service = TaskService(mock_engine)
    assert await task_service.get_task_status_list() == expected_result
