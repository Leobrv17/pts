"""Project schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models.project import ProjectStatus
from app.schemas.sprint import SprintLight, SprintLightResponse
from app.schemas.user import UserResponse


class ProjectBase(BaseModel):
    """Base project schema."""
    centerId: Optional[str] = Field(default=None, description="Service center ID")
    projectName: str = Field(..., min_length=1, max_length=200, description="Project name")
    status: ProjectStatus = Field(..., description="Project status")
    technicalLoadRatio: float = Field(default=1.0, ge=0, description="Transversal vs technical workload ratio")
    taskStatuses: List[str] = Field(default_factory=list, description="The keys to task statuses that should exist in the project.")
    taskTypes: List[str] = Field(default_factory=list, description="The keys to task types that should exist in the project.")


class ProjectTransversalActivityBase(BaseModel):
    """Base schema for project transversal activity."""
    projectId: str = Field(..., description="Project ID")
    activity: str = Field(..., min_length=1, description="Activity name")
    meaning: Optional[str] = Field(default="", description="Activity description")


class ProjectTransversalActivityResponse(BaseModel):
    """Schema for project transversal activity response."""
    id: Optional[str] = Field(alias="_id")
    name: str = Field(..., min_length=1, description="Activity name")
    description: Optional[str] = Field(default="", description="Activity description")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectTransversalActivityUpdate(BaseModel):
    """Schema for project transversal activity update."""
    id: Optional[str] = Field(None, description="Activity ID")
    name: str = Field(..., min_length=1, description="Activity name")
    description: Optional[str] = Field(default="", description="Activity description")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    id: str = Field(..., description="Project ID")
    centerId: Optional[str] = None
    projectName: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ProjectStatus] = None
    technicalLoadRatio: Optional[float] = Field(None, ge=0)
    taskStatuses: Optional[List[str]] = Field(None, description="Existing task statuses")
    taskTypes: Optional[List[str]] = Field(None, description="Existing task types")
    transversalActivities: Optional[List[ProjectTransversalActivityUpdate]] = Field(default_factory=list)


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: str = Field(alias="_id")
    sprints: Optional[List[SprintLightResponse]] = Field(default_factory=list)
    users: List[UserResponse] = Field(default_factory=list)
    transversalActivities: List[ProjectTransversalActivityResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectListResponse(BaseModel):
    """Schema for project list response."""
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    centerId: str = Field(..., description="Project parent Service Center ID")
    projectName: str = Field(..., description="Project name")
    status: str = Field(..., description="Project current status")
    sprints: Optional[List[SprintLight]] = Field(None, description="Project sprints in light version")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }


class ProjectLightResponse(BaseModel):
    """Light schema for project with only basic information."""
    id: str = Field(..., description="Project ID")
    centerId: str = Field(..., description="Project parent Service Center ID")
    projectName: str = Field(..., description="Project name")
    status: str = Field(..., description="Project current status")
    sprints: Optional[List[SprintLightResponse]] = Field(None, description="Project sprints in light version")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }


class ProjectListResponseLight(BaseModel):
    """Schema for projectInfo list response."""
    projects: List[ProjectLightResponse]
    total: int
    page: int
    size: int
    pages: int


class ProjectTransversalActivityCreate(ProjectTransversalActivityBase):
    """Schema for creating a project transversal activity."""
    pass
