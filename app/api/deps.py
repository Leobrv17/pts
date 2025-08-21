"""API dependencies."""

from odmantic import AIOEngine
from fastapi import Depends

from app.core.database import get_database
from app.services.user_service import UserService
from app.services.task_service import TaskService
from app.services.sprint_service import SprintService
from app.services.project_service import ProjectService
from app.services.service_center_service import ServiceCenterService


def get_user_service(engine: AIOEngine = Depends(get_database)) -> UserService:
    """Get user service instance."""
    return UserService(engine)


def get_task_service(engine: AIOEngine = Depends(get_database)) -> TaskService:
    """Get task service instance."""
    return TaskService(engine)


def get_sprint_service(engine: AIOEngine = Depends(get_database)) -> SprintService:
    """Get sprint service instance."""
    return SprintService(engine)


def get_project_service(engine: AIOEngine = Depends(get_database)) -> ProjectService:
    """Get project service instance."""
    return ProjectService(engine)


def get_service_center_service(engine: AIOEngine = Depends(get_database)) -> ServiceCenterService:
    """Get service center service instance."""
    return ServiceCenterService(engine)