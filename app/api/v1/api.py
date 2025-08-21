"""API router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import users, tasks, sprints, projects, service_centers


api_router = APIRouter()

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"]
)

api_router.include_router(
    sprints.router,
    prefix="/sprints",
    tags=["sprints"]
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    service_centers.router,
    prefix="/service-centers",
    tags=["service-centers"]
)