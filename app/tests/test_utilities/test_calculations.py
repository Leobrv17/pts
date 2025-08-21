from datetime import datetime, timezone
from math import floor
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.models.project import Project, ProjectStatus
from app.models.sprint import SprintStatus, SprintTransversalActivity, Sprint
from app.models.task import Task, TaskStatus, TASKRFT
import app.utils.calculations as calc

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INITIAL_DATA_JSON = f"{PROJECT_ROOT}/data/initial_data.json"

sample_project_data = {
    "projectName": "Test Project",
    "status": ProjectStatus.INPROGRESS,
    "roles": ["Developer", "Project Manager"]
}

sample_sprint_data = {
    "projectId": str(ObjectId()),
    "sprintName": "Sprint 1",
    "status": SprintStatus.TODO,
    "startDate": datetime.now(timezone.utc).isoformat(),
    "dueDate": datetime.now(timezone.utc).isoformat(),
    "duration": 10,
    "capacity": 40.0
}

sample_sprint_trans_act_data = {
    "sprintId": str(ObjectId()),
    "activity": "Test activity",
}

sample_task_data = {
    "sprintId": str(ObjectId()),
    "projectId": str(ObjectId()),
    "key": "TASK0",
    "summary": "Task summary",
    "storyPoints": 10.0,
    "progress": 50,
    "assignee": ["62d8ee7f7c4a1b5556f2b70c"],
    "rft": TASKRFT.OK,
}


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.insert_one = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_calculate_sprint_metrics(mock_engine):
    "Test successful calculation of sprint metrics"
    mock_sprint = Sprint(**sample_sprint_data, id=ObjectId())
    mock_tasks = [Task(**sample_task_data, id=ObjectId()) for _ in range(2)]
    mock_trans_act = SprintTransversalActivity(**sample_sprint_trans_act_data, id=ObjectId())

    mock_trans_act.time_spent = 15.0
    mock_tasks[0].status = TaskStatus.DONE
    mock_tasks[0].deliverySprint = mock_sprint.sprintName
    mock_tasks[0].timeSpent = 5.0
    mock_sprint.status = SprintStatus.DONE

    mock_sprint.task = [task.id for task in mock_tasks]
    mock_sprint.sprint_transversal_activities = [mock_trans_act.id]

    mock_engine.find.return_value = mock_tasks
    mock_engine.find_one.return_value = mock_trans_act

    metrics = await calc.calculate_sprint_metrics(mock_sprint, [mock_trans_act], mock_tasks)

    assert isinstance(metrics, dict)

    expected_metrics = {
        "scoped": round(len(mock_tasks)*mock_tasks[0].storyPoints,1),
        "velocity": floor(mock_tasks[0].storyPoints),
        "progress": floor(mock_tasks[0].progress),
        "technical_time_spent": mock_tasks[0].timeSpent,
        "transversal_time_spent": mock_trans_act.time_spent,
        "time_spent": mock_tasks[0].timeSpent + mock_trans_act.time_spent,
        "duration": 0,
        "otd": 100 * mock_tasks[0].storyPoints / (len(mock_tasks)*mock_tasks[0].storyPoints),
        "oqd": 100
    }

    assert metrics == expected_metrics


@pytest.mark.asyncio
async def test_calculate_sprint_metrics_no_tasks(mock_engine):
    "Test successful calculation of sprint metrics if no tasks are in the sprint"
    mock_sprint = Sprint(**sample_sprint_data, id=ObjectId())
    mock_engine.find.return_value = None

    metrics = await calc.calculate_sprint_metrics(mock_sprint, [], [])

    expected_metrics = {
        "scoped": 0,
        "velocity": 0,
        "progress": 0,
        "time_spent": 0.0,
        "duration": 0,
        "otd": 0.0,
        "oqd": 0.0
    }

    assert metrics == expected_metrics


@pytest.mark.asyncio
async def test_calculate_task_metrics(mock_engine):
    "Test successful calculation of task metrics"
    dummy_project = Project(**sample_project_data)
    dummy_project.transversal_vs_technical_workload_ratio = 2.0

    task_id = ObjectId()
    mock_task = Task(**sample_task_data, id=task_id)
    mock_task.timeSpent = 2.0
    mock_task.timeRemaining = 8.0
    expected_technical_load = mock_task.storyPoints / dummy_project.transversal_vs_technical_workload_ratio
    expected_delta = expected_technical_load - (mock_task.timeSpent + mock_task.timeRemaining)
    expected_progress = 100 * (mock_task.timeSpent / (mock_task.timeSpent + mock_task.timeRemaining))

    mock_engine.find_one.side_effect = [mock_task, dummy_project]

    metrics = await calc.calculate_task_metrics(mock_task, dummy_project.transversal_vs_technical_workload_ratio)

    assert isinstance(metrics, dict)
    assert metrics["technical_load"] == expected_technical_load
    assert metrics["delta"] == expected_delta
    assert metrics["progress"] == expected_progress


@pytest.mark.asyncio
async def test_calculate_task_metrics_no_time(mock_engine):
    "Test successful calculation of task metrics if no times are set"
    dummy_project = Project(**sample_project_data)
    dummy_project.transversal_vs_technical_workload_ratio = 2.0

    task_id = ObjectId()
    mock_task = Task(**sample_task_data, id=task_id)

    mock_engine.find_one.side_effect = [mock_task, dummy_project]

    metrics = await calc.calculate_task_metrics(mock_task, dummy_project.transversal_vs_technical_workload_ratio)

    assert isinstance(metrics, dict)
    assert metrics["technical_load"] == mock_task.storyPoints / dummy_project.transversal_vs_technical_workload_ratio
    assert metrics["delta"] == metrics["technical_load"]
    assert metrics["progress"] == 0.0


@pytest.mark.asyncio
async def test_calculate_story_points():
    "Test successful addition of story points"
    task1 = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        storyPoints=2,
        progress=50,
        key="TASK1",
        timeSpent=1,
        rft=TASKRFT.OK,
    )

    task2 = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        storyPoints=1,
        progress=100,
        key="TASK2",
        timeSpent=3,
        rft=TASKRFT.OK,
    )

    assert await calc.calculate_story_points([task1, task2]) == 3
    assert await calc.calculate_story_points([]) == 0


@pytest.mark.asyncio
async def test_calculate_sprint_progress():
    "Test successful calculations of progress"
    task_inprogress = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        storyPoints=2,
        progress=50,
        key="TASK1",
        timeSpent=1,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.OK,
    )

    task_done = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        storyPoints=1,
        progress=100,
        key="TASK2",
        timeSpent=3,
        status=TaskStatus.DONE,
        rft=TASKRFT.OK,
    )

    task_cancelled = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        storyPoints=10,
        progress=100,
        key="TASK3",
        timeSpent=3,
        status=TaskStatus.CANCELLED,
        rft=TASKRFT.OK,
    )

    assert await calc.calculate_progress([task_inprogress, task_done]) == 200/3
    assert await calc.calculate_progress([task_inprogress, task_done, task_cancelled]) == 200/3
    assert await calc.calculate_progress(None) == 100


@pytest.mark.asyncio
async def test_calculate_velocity():
    task1 = Task(           # deliverySprint is current sprint but not Done
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK1",
        storyPoints=1,
        status=TaskStatus.INPROGRESS,
        deliverySprint="sprint",
        rft=TASKRFT.OK,
    )
    task2 = Task(           # Done and deliverySprint is current sprint (only this should be added)
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK1",
        status=TaskStatus.DONE,
        storyPoints=3,
        deliverySprint="sprint",
        rft=TASKRFT.OK,
    )
    task3 = Task(           # Done, but deliverySprint is None
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK1",
        storyPoints=5,
        status=TaskStatus.DONE,
        rft=TASKRFT.OK,
    )

    assert await calc.calculate_velocity([task1,task2,task3], "sprint") == 3
    assert await calc.calculate_velocity([], "sprint") == 0


@pytest.mark.asyncio
async def test_calculate_total_time():
    "Test successful calculation of total time on a given sprint"
    task1 = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK1",
        timeSpent=1.63,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.OK,
    )

    task2 = Task(
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK2",
        timeSpent=3.14,
        status=TaskStatus.DONE,
        rft=TASKRFT.OK,
    )

    assert await calc.calculate_total_time(None) == 0.0
    assert await calc.calculate_total_time([task1,task2]) == 4.77

@pytest.mark.asyncio
async def test_calculate_transversal_time():
    "Test successful calculation of transversal time on a given sprint"
    sprint1 = SprintTransversalActivity(
        sprintId=ObjectId(),
        activity="activity",
        time_spent=3.0
    )

    sprint2 = SprintTransversalActivity(
        sprintId=ObjectId("675c247a2d3ce9698c92f068"),
        activity="acitivityr",
        time_spent=5.0,
    )

    assert await calc.calculate_transversal_time(None) == 0
    assert await calc.calculate_transversal_time([sprint1,sprint2]) == 8.0


@pytest.mark.asyncio
async def test_calculate_otd():
    "Test successful calculation of sprint OTD in percentage"
    velocity = 2.5
    in_scope = 10

    assert await calc.calculate_otd(SprintStatus.DONE, velocity, in_scope) == 25            # assert successful calculation
    assert await calc.calculate_otd(SprintStatus.INPROGRESS, velocity, in_scope) == 0.0     # assert no calculation if sprint status not done

    in_scope = 0.0

    assert await calc.calculate_otd(SprintStatus.DONE, velocity, in_scope) == 0.0           # assert no calculation if no SP in sprint


@pytest.mark.asyncio
async def test_calculate_oqd():
    current_sprint_name = "current"

    task1 = Task(       # Should not count because task is not done.
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK1",
        deliverySprint=current_sprint_name,
        status=TaskStatus.INPROGRESS,
        rft=TASKRFT.KO,
    )

    task2 = Task(       # Should count
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK2",
        deliverySprint=current_sprint_name,
        status=TaskStatus.DONE,
        rft=TASKRFT.OK,
    )

    task3 = Task(       # Should count
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK3",
        deliverySprint=current_sprint_name,
        status=TaskStatus.DONE,
        rft=TASKRFT.KO,
    )

    task4 = Task(       # Should count
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK4",
        deliverySprint=current_sprint_name,
        status=TaskStatus.DONE,
        rft=TASKRFT.DEFAULT,
    )

    task5 = Task(       # Should not count because deliverySprint is not current
        sprintId=ObjectId("67043935189669a4d9d1c0bc"),
        projectId=ObjectId("67043935189669a4d9d1c0bd"),
        summary="Task summary",
        key="TASK5",
        status=TaskStatus.DONE,
        deliverySprint="not_current",
        rft=TASKRFT.DEFAULT,
    )

    tasks = [task1,task2,task3,task4,task5]

    assert await calc.calculate_oqd(current_sprint_name, SprintStatus.DONE, tasks) == 100/3           # assert successful calculation
    assert await calc.calculate_oqd(current_sprint_name, SprintStatus.DONE, []) == 0            # assert no calculation if no tasks
    assert await calc.calculate_oqd(current_sprint_name, SprintStatus.TODO, tasks) == 0               # assert no calculation if sprint not Done
    assert await calc.calculate_oqd(current_sprint_name, SprintStatus.DONE, [task1]) == 0       # assert no calculation if no tasks Done


def test_date_conversion():
    "Test successful conversion of string to datetime"
    start_date = datetime(2025,7,30)
    due_date = datetime(2025,8,30)
    assert calc.date_convertion(start_date, due_date) == ("2025-07-30T00:00:00.000000Z","2025-08-30T00:00:00.000000Z")


def test_calculate_weekdays():
    "Test successful calculation of the amount of weekdays in a given sprint, given its start and due dates"
    start_date = datetime(2025,2,4)     # Some Tuesday
    due_date = datetime(2025,2,11)      # Next Tuesday
    weekdays = calc.calculate_weekdays(start_date, due_date)

    assert weekdays == 5        # Test for expected start and due dates

    start_date = datetime(2025,2,9)     # Some Saturday
    due_date = datetime(2025,2,16)      # Next Sunday
    weekdays = calc.calculate_weekdays(start_date, due_date)

    assert weekdays == 5        # Fool-proof test if start or due dates are set during a weekend day

    start_date = datetime(2025,2,6)     # Some Thursday
    due_date = datetime(2025,2,4)       # Previous Tuesday
    weekdays = calc.calculate_weekdays(start_date, due_date)

    assert weekdays == 2        # Test if start date is set after due date (should reorder them)
