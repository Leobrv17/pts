from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.models.project import ProjectStatus, Project, ProjectTransversalActivity
from app.schemas.project import ProjectBase, ProjectUpdate, ProjectTransversalActivityUpdate, ProjectTransversalActivityCreate
from app.services.project_service import ProjectService


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.insert_one = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_create_project(mock_engine):
    """Test POST api/projects/ service-side"""
    project_data = ProjectBase(
        centerId=str(ObjectId()),
        projectName="Test project",
        status=ProjectStatus.INPROGRESS,
        technicalLoadRatio=2.0,
        taskStatuses=["Done", "To do", "In progress"],
        taskTypes=["Task", "Bug"]
    )

    mock_engine.save.return_value = None
    project_service = ProjectService(mock_engine)
    created_project = await project_service.create_project(project_data)

    expected_result = Project(
        id=created_project.id,
        projectName=project_data.projectName,
        status=project_data.status,
        sprints=[],
        centerId=project_data.centerId,
        users=[],
        created_at=created_project.created_at,
        transversal_vs_technical_workload_ratio=project_data.technicalLoadRatio,
        project_transversal_activities=[],
        task_types=project_data.taskTypes,
        task_statuses=project_data.taskStatuses
    )

    assert expected_result == created_project


@pytest.mark.asyncio
async def test_get_project_by_id_no_project(mock_engine):
    """Test get_project_by_id with project not found"""
    mock_engine.find_one.return_value = None
    project_service = ProjectService(mock_engine)
    with pytest.raises(HTTPException):
        await project_service.get_project_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_get_projects(mock_engine):
    """Test GET api/projects/ service-side"""
    center_id = ObjectId()
    project1 = Project(
        id=ObjectId(),
        projectName="Project 1",
        status=ProjectStatus.INPROGRESS,
        sprints=[],
        centerId=center_id,
        users=[],
        transversal_vs_technical_workload_ratio=1,
        project_transversal_activities=[],
        taskStatuses=["Done", "To do", "In progress"],
        taskTypes=["Task", "Bug"]
    )
    project2 = Project(
        id=ObjectId(),
        projectName="Project 2",
        status=ProjectStatus.DONE,
        sprints=[],
        centerId=center_id,
        users=[],
        transversal_vs_technical_workload_ratio=1,
        project_transversal_activities=[],
        taskStatuses=["Done", "To do", "In progress"],
        taskTypes=["Task", "Bug"]
    )

    mock_engine.find.return_value = [p for p in [project1, project2]
                                     if p.status == ProjectStatus.INPROGRESS
                                     and p.centerId == center_id]
    project_service = ProjectService(mock_engine)
    projects_found, _ = await project_service.get_projects(
        center_id=str(center_id),
        status="In progress"
    )

    assert projects_found == [project1]


@pytest.mark.asyncio
async def test_update_project(mock_engine):
    """Test PUT api/projects/ service-side"""
    project = Project(
        id=ObjectId(),
        projectName="Project 1",
        status=ProjectStatus.INPROGRESS,
        sprints=[],
        centerId=ObjectId(),
        users=[],
        transversal_vs_technical_workload_ratio=1,
        project_transversal_activities=[],
        taskStatuses=["Done", "To do", "In progress"],
        taskTypes=["Task", "Bug"]
    )
    update_data = ProjectUpdate(
        id=str(project.id),
        centerId=str(ObjectId()),
        projectName="New project name",
        transversalActivities=[ProjectTransversalActivityUpdate(
            name="act",
            description="desc"
        )]  # Should not have an effect here
    )

    mock_engine.find_one.return_value = project
    project_service = ProjectService(mock_engine)
    updated_project = await project_service.update_project(update_data)

    expected_result = Project(
        id=project.id,
        projectName=update_data.projectName,
        status=project.status,
        sprints=[],
        centerId=ObjectId(update_data.centerId),
        users=[],
        created_at=project.created_at,
        transversal_vs_technical_workload_ratio=project.transversal_vs_technical_workload_ratio,
        project_transversal_activities=[],
        task_types=project.task_types,
        task_status=project.task_statuses
    )

    assert expected_result == updated_project


@pytest.mark.asyncio
async def test_delete_project(mock_engine):
    """Test DELETE api/projects/ service-side"""
    project = Project(
        id=ObjectId(),
        projectName="Project 1",
        status=ProjectStatus.INPROGRESS,
        sprints=[],
        centerId=ObjectId(),
        users=[],
        transversal_vs_technical_workload_ratio=1,
        project_transversal_activities=[],
        taskStatuses=["Done", "To do", "In progress"],
        taskTypes=["Task", "Bug"],
        is_deleted=False
    )

    mock_engine.find_one.return_value = project
    mock_engine.save.return_value = project
    project_service = ProjectService(mock_engine)
    assert await project_service.delete_project(str(project.id))
    assert project.is_deleted


@pytest.mark.asyncio
async def test_create_project_ta(mock_engine):
    """Test create_project_ta service"""
    ta = ProjectTransversalActivityCreate(
        projectId=str(ObjectId()),
        activity="Act",
        meaning="desc"
    )

    mock_engine.save.return_value = None
    project_service = ProjectService(mock_engine)
    created_act = await project_service.create_project_transversal_activity(ta)

    expected_result = ProjectTransversalActivity(
        id=created_act.id,
        project_id=ObjectId(ta.projectId),
        activity=ta.activity,
        meaning=ta.meaning,
        created_at=created_act.created_at
    )

    assert created_act == expected_result


@pytest.mark.asyncio
async def test_get_project_ta_by_id_no_act(mock_engine):
    """Test get_project_ta_by_id with activity not found"""
    mock_engine.find_one.return_value = None
    project_service = ProjectService(mock_engine)
    with pytest.raises(HTTPException):
        await project_service.get_project_transversal_activity_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_get_project_tas_by_project(mock_engine):
    """Test get_project_transversal_activities_by_project"""
    project_id = ObjectId()
    ta1 = ProjectTransversalActivity(
        id=ObjectId(),
        project_id=project_id,
        activity="Act1",
        meaning="desc1",
    )
    ta2 = ProjectTransversalActivity(
        id=ObjectId(),
        project_id=ObjectId(),
        activity="Act2",
        meaning="desc2",
    )

    mock_engine.find.return_value = [ta for ta in [ta1, ta2] if ta.project_id == project_id]
    project_service = ProjectService(mock_engine)
    tas_found = await project_service.get_project_transversal_activities_by_project(str(project_id))

    assert tas_found == [ta1]


@pytest.mark.asyncio
async def test_update_project_ta(mock_engine):
    """Test update_project_ta service"""
    ta = ProjectTransversalActivity(
        id=ObjectId(),
        project_id=ObjectId(),
        activity="Test act",
        meaning="za description"
    )
    ta_update = ProjectTransversalActivity(
        id=str(ta.id),
        project_id=ta.project_id,
        activity="New act name",
        meaning="new desc"
    )

    mock_engine.save.return_value = None
    mock_engine.find_one.return_value = ta
    project_service = ProjectService(mock_engine)
    updated_ta = await project_service.update_project_transversal_activity(ta_update)

    expected_result = ProjectTransversalActivity(
        id=ta.id,
        project_id=ta.project_id,
        activity=ta_update.activity,
        meaning=ta_update.meaning,
        created_at=ta.created_at
    )
    assert expected_result == updated_ta


@pytest.mark.asyncio
async def test_delete_project_ta(mock_engine):
    """Test delete_project_ta service"""
    ta = ProjectTransversalActivity(
        id=ObjectId(),
        project_id=ObjectId(),
        activity="Test act",
        meaning="za description",
        is_deleted=False
    )

    mock_engine.save.return_value = ta
    mock_engine.find_one.return_value = ta
    project_service = ProjectService(mock_engine)
    assert await project_service.delete_project_transversal_activity(str(ta.id))
    assert ta.is_deleted
