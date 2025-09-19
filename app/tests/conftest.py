"""Configuration globale des tests et fixtures communes."""

import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Generator

from app.models.project import Project, ProjectStatus, ProjectTransversalActivity
from app.models.service_center import ServiceCenter, ServiceCenterStatus
from app.models.sprint import Sprint, SprintStatus, SprintTransversalActivity
from app.models.task import Task, TaskStatus, TaskType, TASKRFT, TaskDeliveryStatus
from app.models.user import User, UserTypeEnum, DirectorAccess, ProjectAccess, AccessLevelEnum


@pytest.fixture
def mock_engine() -> AsyncMock:
    """Mock de l'engine ODMantic pour tous les tests."""
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.count = AsyncMock()
    engine.save_all = AsyncMock()
    return engine


@pytest.fixture
def valid_object_id() -> ObjectId:
    """ObjectId valide pour les tests."""
    return ObjectId()


@pytest.fixture
def another_object_id() -> ObjectId:
    """Deuxième ObjectId valide pour les tests."""
    return ObjectId()


@pytest.fixture
def sample_datetime() -> datetime:
    """DateTime de référence pour les tests."""
    return datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_future_datetime(sample_datetime) -> datetime:
    """DateTime future pour les tests."""
    return sample_datetime + timedelta(days=14)


# === FIXTURES POUR LES MODÈLES ===

@pytest.fixture
def sample_service_center(valid_object_id) -> ServiceCenter:
    """Service center de test."""
    return ServiceCenter(
        id=valid_object_id,
        centerName="Test Center",
        location="Toulouse, France",
        contactEmail="test@sii.fr",
        contactPhone="0123456789",
        status=ServiceCenterStatus.OPERATIONAL,
        projects=[],
        users=[],
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={}
    )


@pytest.fixture
def sample_project(valid_object_id, another_object_id) -> Project:
    """Projet de test."""
    return Project(
        id=valid_object_id,
        centerId=another_object_id,
        projectName="Test Project",
        status=ProjectStatus.INPROGRESS,
        sprints=[],
        users=[],
        transversal_vs_technical_workload_ratio=2.0,
        project_transversal_activities=[],
        task_statuses=["TODO", "PROG", "DONE"],
        task_types=["TASK", "BUG"]
    )


@pytest.fixture
def sample_sprint(valid_object_id, another_object_id, sample_datetime, sample_future_datetime) -> Sprint:
    """Sprint de test."""
    return Sprint(
        id=valid_object_id,
        projectId=another_object_id,
        sprintName="Test Sprint",
        status=SprintStatus.TODO,
        startDate=sample_datetime,
        dueDate=sample_future_datetime,
        capacity=40.0,
        sprint_transversal_activities=[],
        task=[],
        task_statuses=["TODO", "PROG", "DONE"],
        task_types=["TASK", "BUG"]
    )


@pytest.fixture
def sample_task(valid_object_id, another_object_id) -> Task:
    """Tâche de test."""
    third_id = ObjectId()
    return Task(
        id=valid_object_id,
        sprintId=another_object_id,
        projectId=third_id,
        key="TEST-001",
        summary="Test Task Summary",
        storyPoints=5.0,
        wu="",
        comment="Test comment",
        deliveryStatus=TaskDeliveryStatus.DEFAULT,
        deliveryVersion="",
        type=TaskType.TASK,
        status=TaskStatus.TODO,
        rft=TASKRFT.DEFAULT,
        technicalLoad=2.5,
        timeSpent=0.0,
        timeRemaining=2.5,
        progress=0.0,
        assignee=[],
        delta=0.0
    )


@pytest.fixture
def sample_user(valid_object_id) -> User:
    """Utilisateur de test."""
    return User(
        id=valid_object_id,
        first_name="John",
        family_name="Doe",
        email="john.doe@sii.fr",
        type=UserTypeEnum.NORMAL,
        registration_number="123456",
        trigram="JDO",
        director_access_list=[],
        project_access_list=[]
    )


@pytest.fixture
def sample_project_transversal_activity(valid_object_id, another_object_id) -> ProjectTransversalActivity:
    """Activité transversale de projet de test."""
    return ProjectTransversalActivity(
        id=valid_object_id,
        project_id=another_object_id,
        activity="Test Activity",
        meaning="Test activity description",
        default=True
    )


@pytest.fixture
def sample_sprint_transversal_activity(valid_object_id, another_object_id) -> SprintTransversalActivity:
    """Activité transversale de sprint de test."""
    return SprintTransversalActivity(
        id=valid_object_id,
        sprintId=another_object_id,
        activity="Test Sprint Activity",
        meaning="Test sprint activity description",
        time_spent=2.5
    )


@pytest.fixture
def sample_director_access(valid_object_id, another_object_id) -> DirectorAccess:
    """Accès directeur de test."""
    return DirectorAccess(
        id=valid_object_id,
        user_id=another_object_id,
        service_center_id=ObjectId(),
        service_center_name="Test Center"
    )


@pytest.fixture
def sample_project_access(valid_object_id, another_object_id) -> ProjectAccess:
    """Accès projet de test."""
    return ProjectAccess(
        id=valid_object_id,
        user_id=another_object_id,
        service_center_id=ObjectId(),
        service_center_name="Test Center",
        project_id=ObjectId(),
        project_name="Test Project",
        access_level=AccessLevelEnum.TEAM_MEMBER,
        occupancy_rate=50.0
    )


# === FIXTURES POUR LES LISTES ===

@pytest.fixture
def sample_tasks_list(sample_task) -> list[Task]:
    """Liste de tâches pour les tests."""
    task1 = sample_task
    task2 = Task(
        id=ObjectId(),
        sprintId=sample_task.sprintId,
        projectId=sample_task.projectId,
        key="TEST-002",
        summary="Second Test Task",
        storyPoints=3.0,
        status=TaskStatus.DONE,
        type=TaskType.BUG,
        technicalLoad=1.5,
        timeSpent=1.5,
        timeRemaining=0.0,
        progress=100.0,
        assignee=[],
        delta=0.0
    )
    return [task1, task2]


@pytest.fixture
def sample_projects_list(sample_project) -> list[Project]:
    """Liste de projets pour les tests."""
    project1 = sample_project
    project2 = Project(
        id=ObjectId(),
        centerId=sample_project.centerId,
        projectName="Second Test Project",
        status=ProjectStatus.DONE,
        sprints=[],
        users=[],
        transversal_vs_technical_workload_ratio=1.5,
        project_transversal_activities=[],
        task_statuses=["TODO", "DONE"],
        task_types=["TASK"]
    )
    return [project1, project2]


# === FIXTURES D'ERREURS POUR LES TESTS NÉGATIFS ===

@pytest.fixture
def invalid_object_id() -> str:
    """ObjectId invalide pour tester les erreurs."""
    return "invalid_id_format"


@pytest.fixture
def nonexistent_object_id() -> str:
    """ObjectId qui n'existe pas en base."""
    return str(ObjectId())


# === FIXTURES POUR LES MOCK DE DONNÉES ===

@pytest.fixture
def mock_task_metrics() -> dict:
    """Métriques de tâche mockées."""
    return {
        "technical_load": 2.5,
        "time_spent": 1.0,
        "updated": 2.5,
        "delta": 0.0,
        "progress": 40.0
    }


@pytest.fixture
def mock_sprint_metrics() -> dict:
    """Métriques de sprint mockées."""
    return {
        "duration": 10.0,
        "scoped": 8.0,
        "velocity": 5.0,
        "progress": 62.5,
        "time_spent": 15.0,
        "otd": 62.5,
        "oqd": 80.0
    }