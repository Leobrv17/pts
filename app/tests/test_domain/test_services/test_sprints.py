from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.models.sprint import SprintStatus, Sprint, SprintTransversalActivity
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintTransversalActivityUpdate
from app.services.sprint_service import SprintService


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.insert_one = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_create_sprint(mock_engine):
    """Test POST api/sprints/ service-side"""
    sprint_create = SprintCreate(
        projectId=str(ObjectId()),
        capacity=15,
        sprintName="Test Sprint",
        status=SprintStatus.INPROGRESS,
        startDate=datetime(2025,8,13),
        dueDate=datetime(2025,8,20)
    )

    mock_engine.save.return_value = None
    sprint_service = SprintService(mock_engine)
    created_sprint = await sprint_service.create_sprint(sprint_create)

    expected_result = Sprint(
        id=created_sprint.id,
        projectId=ObjectId(sprint_create.projectId),
        sprintName=sprint_create.sprintName,
        status=sprint_create.status,
        startDate=sprint_create.startDate,
        dueDate=sprint_create.dueDate,
        capacity=sprint_create.capacity,
        sprint_transversal_activities=[],
        task=[],
        created_at=created_sprint.created_at,
        task_statuses=[],
        task_types=[]
    )

    assert created_sprint == expected_result


@pytest.mark.asyncio
async def test_get_sprint_by_id_not_found(mock_engine):
    """Test get_sprint_by_id exception"""
    mock_engine.find_one.return_value = None
    sprint_service = SprintService(mock_engine)

    with pytest.raises(HTTPException):
        await sprint_service.get_sprint_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_get_sprints(mock_engine):
    """Test GET api/sprints/ service-side"""
    project_id = ObjectId()
    sprint1_id = ObjectId()
    sprint2_id = ObjectId()

    sprint1 = Sprint(
        id=sprint1_id,
        projectId=project_id,
        sprintName="Sprint 1",
        status=SprintStatus.TODO,
        startDate=datetime.now(),
        dueDate=datetime.now(),
        capacity=15,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=[],
        task_types=[]
    )
    sprint2 = Sprint(
        id=sprint2_id,
        projectId=project_id,
        sprintName="Sprint 2",
        status=SprintStatus.INPROGRESS,
        startDate=datetime.now(),
        dueDate=datetime.now(),
        capacity=10,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=[],
        task_types=[]
    )
    sprints_found = [s for s in [sprint1, sprint2] if s.status == SprintStatus.TODO
                     and s.projectId == project_id
                     and s.id in [sprint1_id, sprint2_id]]
    mock_engine.find.return_value = sprints_found
    sprint_service = SprintService(mock_engine)
    sprints, amount = await sprint_service.get_sprints(
        sprint_ids=[str(sprint1_id), str(sprint2_id)],
        project_id=str(project_id),
        status="To do"
    )

    assert amount == 1
    assert sprints == [sprint1]


@pytest.mark.asyncio
async def test_get_relevant_sprints_by_project(mock_engine):
    """Test get_relevant_sprints_by_project service"""
    project_id = ObjectId()
    sprint1_id = ObjectId()
    sprint2_id = ObjectId()

    sprint1 = Sprint(
        id=sprint1_id,
        projectId=project_id,
        sprintName="Sprint 1",
        status=SprintStatus.TODO,
        startDate=datetime.now(),
        dueDate=datetime.now(),
        capacity=15,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=[],
        task_types=[]
    )
    sprint2 = Sprint(
        id=sprint2_id,
        projectId=project_id,
        sprintName="Sprint 2",
        status=SprintStatus.INPROGRESS,
        startDate=datetime.now(),
        dueDate=datetime.now(),
        capacity=10,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=[],
        task_types=[]
    )

    mock_engine.find.return_value = [sprint1, sprint2]
    sprint_service = SprintService(mock_engine)
    response = await sprint_service.get_relevant_sprints_by_project(str(project_id))

    expected_response = [
        {"id": str(sprint1_id), "name":sprint1.sprintName},
        {"id": str(sprint2_id), "name": sprint2.sprintName},
    ]

    assert expected_response == response


@pytest.mark.asyncio
async def test_update_sprint(mock_engine):
    """Test PUT api/sprints/"""
    og_sprint = Sprint(
        id=ObjectId(),
        projectId=ObjectId(),
        sprintName="Test sprint",
        status=SprintStatus.TODO,
        startDate=datetime.now(),
        dueDate=datetime.now(),
        capacity=15,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=[],
        task_types=[]
    )

    sprint_update = SprintUpdate(
        id=str(og_sprint.id),
        projectId=str(ObjectId()),
        sprintName="New sprint name",
        status=SprintStatus.INPROGRESS,
        startDate=datetime(2025,8,1),
        capacity=10,
        transversalActivities=[SprintTransversalActivityUpdate(
            name="Activity",
            description="description",
            timeSpent=12
        )]  # must not be added by this service
    )

    mock_engine.find_one.return_value = og_sprint
    sprint_service = SprintService(mock_engine)
    updated_sprint = await sprint_service.update_sprint(sprint_update)

    expected_result = Sprint(
        id=og_sprint.id,
        projectId=ObjectId(sprint_update.projectId),
        sprintName=sprint_update.sprintName,
        status=sprint_update.status,
        startDate=sprint_update.startDate,
        dueDate=og_sprint.dueDate,
        capacity=sprint_update.capacity,
        sprint_transversal_activities=[],
        task=[],
        created_at=og_sprint.created_at,
        task_statuses=[],
        task_types=[]
    )

    assert expected_result == updated_sprint


@pytest.mark.asyncio
async def test_get_sprint_by_id_no_sprint(mock_engine):
    """Test get_sprint_by_id with no sprint found"""
    mock_engine.find_one.return_value = None
    sprint_service = SprintService(mock_engine)
    with pytest.raises(HTTPException):
        await sprint_service.get_sprint_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_delete_sprint(mock_engine):
    """Test DELETE api/sprints/{sprintId}"""
    og_sprint = Sprint(
        id=ObjectId(),
        projectId=ObjectId(),
        sprintName="Test sprint",
        status=SprintStatus.TODO,
        startDate=datetime.now(),
        dueDate=datetime.now(),
        capacity=15,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=[],
        task_types=[],
        is_deleted=False
    )

    mock_engine.find_one.return_value = og_sprint
    mock_engine.save.return_value = og_sprint
    sprint_service = SprintService(mock_engine)
    assert await sprint_service.delete_sprint(str(og_sprint.id))
    assert og_sprint.is_deleted


@pytest.mark.asyncio
async def test_create_sprint_ta(mock_engine):
    """Test create_sprint_transversal_activity service"""
    ta = SprintTransversalActivity(
        sprintId = ObjectId(),
        activity="Test act",
        meaning="za description",
        time_spent=12
    )

    mock_engine.save.return_value = None
    sprint_service = SprintService(mock_engine)
    created_activity = await sprint_service.create_sprint_transversal_activity(ta)

    assert created_activity == ta


@pytest.mark.asyncio
async def test_update_sprint_ta(mock_engine):
    """Test update_sprint_transversal_activity service"""
    ta = SprintTransversalActivity(
        id=ObjectId(),
        sprintId=ObjectId(),
        activity="Test act",
        meaning="za description",
        time_spent=12
    )
    ta_update = SprintTransversalActivityUpdate(
        id=str(ta.id),
        name="New act name",
        description="new desc",
        timeSpent=13
    )

    mock_engine.save.return_value = None
    mock_engine.find_one.return_value = ta
    sprint_service = SprintService(mock_engine)
    updated_ta = await sprint_service.update_sprint_transversal_activity(ta_update)

    expected_result = SprintTransversalActivity(
        id=ta.id,
        sprintId=ta.sprintId,
        activity=ta_update.name,
        meaning=ta_update.description,
        time_spent=ta_update.timeSpent,
        created_at=ta.created_at
    )
    assert expected_result == updated_ta


@pytest.mark.asyncio
async def test_get_sprint_ta_by_id_no_sprint(mock_engine):
    """Test get_sprint_ta_by_id with no sprint found"""
    mock_engine.find_one.return_value = None
    sprint_service = SprintService(mock_engine)
    with pytest.raises(HTTPException):
        await sprint_service.get_sprint_transversal_activity_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_get_sprint_ta_by_id(mock_engine):
    """Test get_sprint_ta_by_id service"""
    ta = SprintTransversalActivity(
        id=ObjectId(),
        sprintId=ObjectId(),
        activity="Test act",
        meaning="za description",
        time_spent=12
    )

    mock_engine.find_one.return_value = ta
    sprint_service = SprintService(mock_engine)
    result = await sprint_service.get_sprint_transversal_activity_by_id(str(ta.id))

    assert result == ta


@pytest.mark.asyncio
async def test_get_sprint_tas_by_sprint(mock_engine):
    """Test get_sprint_tas_by_sprint service"""
    sprint_id = ObjectId()
    ta1 = SprintTransversalActivity(
        id=ObjectId(),
        sprintId=sprint_id,
        activity="Act1",
        meaning="desc1",
        time_spent=11
    )
    ta2 = SprintTransversalActivity(
        id=ObjectId(),
        sprintId=ObjectId(),
        activity="Act2",
        meaning="desc2",
        time_spent=22
    )

    mock_engine.find.return_value = [ta for ta in [ta1, ta2] if ta.sprintId == sprint_id]
    sprint_service = SprintService(mock_engine)
    tas_found = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sprint_id))

    assert tas_found == [ta1]


@pytest.mark.asyncio
async def test_delete_sprint_ta(mock_engine):
    """Test delete_sprint_ta service"""
    ta = SprintTransversalActivity(
        id=ObjectId(),
        sprintId=ObjectId(),
        activity="Act1",
        meaning="desc1",
        time_spent=11,
        is_deleted=False
    )

    mock_engine.find_one.return_value = ta
    mock_engine.save.return_value = ta
    sprint_service = SprintService(mock_engine)
    assert await sprint_service.delete_sprint_transversal_activity(str(ta.id))
    assert ta.is_deleted
