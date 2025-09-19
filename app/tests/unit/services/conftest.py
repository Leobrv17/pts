"""Fixtures spécifiques aux tests des services."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.project_service import ProjectService
from app.services.service_center_service import ServiceCenterService
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.cascade_deletion_service import CascadeDeletionService


@pytest.fixture
def project_service(mock_engine) -> ProjectService:
    """Instance du service Project avec engine mocké."""
    return ProjectService(mock_engine)


@pytest.fixture
def service_center_service(mock_engine) -> ServiceCenterService:
    """Instance du service ServiceCenter avec engine mocké."""
    return ServiceCenterService(mock_engine)


@pytest.fixture
def sprint_service(mock_engine) -> SprintService:
    """Instance du service Sprint avec engine mocké."""
    return SprintService(mock_engine)


@pytest.fixture
def task_service(mock_engine) -> TaskService:
    """Instance du service Task avec engine mocké."""
    return TaskService(mock_engine)


@pytest.fixture
def user_service(mock_engine) -> UserService:
    """Instance du service User avec engine mocké."""
    return UserService(mock_engine)


@pytest.fixture
def cascade_deletion_service(mock_engine) -> CascadeDeletionService:
    """Instance du service CascadeDeletion avec engine mocké."""
    return CascadeDeletionService(mock_engine)


@pytest.fixture
def mock_calculate_task_metrics():
    """Mock pour la fonction calculate_task_metrics."""
    with MagicMock() as mock:
        mock.return_value = {
            "technical_load": 2.5,
            "time_spent": 1.0,
            "updated": 2.5,
            "delta": 0.0,
            "progress": 40.0
        }
        yield mock