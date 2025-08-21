"""Sprint schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models.sprint import SprintStatus
from app.schemas.task import TaskResponse


class SprintBase(BaseModel):
    """Base sprint schema."""
    projectId: str = Field(..., description="Project ID")
    capacity: float = Field(..., ge=0, description="Sprint capacity in man*days")
    sprintName: str = Field(..., min_length=1, max_length=200, description="Sprint name")
    status: SprintStatus = Field(default=SprintStatus.TODO, description="Sprint status")
    startDate: datetime = Field(..., description="Sprint start date")
    dueDate: datetime = Field(..., description="Sprint due date")


class SprintTransversalActivityBase(BaseModel):
    """Base schema for sprint transversal activity."""
    name: str = Field(..., min_length=1, description="Activity name")
    description: Optional[str] = Field(default="", description="Activity description")
    timeSpent: Optional[float] = Field(default=0.0, ge=0, description="Time spent on activity")


class SprintTransversalActivityResponse(SprintTransversalActivityBase):
    """Schema for sprint transversal activity response."""
    id: str = Field(..., description="Activity ID")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class SprintCreate(SprintBase):
    """Schema for creating a sprint."""
    pass


class SprintTransversalActivityUpdate(BaseModel):
    """Schema for updating a sprint transversal activity."""
    id: Optional[str] = Field(None, description="Activity ID")
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    timeSpent: Optional[float] = Field(None, ge=0)


class SprintUpdate(BaseModel):
    """Schema for updating a sprint."""
    id: str = Field(..., description="Sprint ID")
    projectId: Optional[str] = None
    sprintName: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[SprintStatus] = None
    startDate: Optional[datetime] = None
    dueDate: Optional[datetime] = None
    capacity: Optional[float] = Field(None, ge=0)
    transversalActivities: Optional[List[SprintTransversalActivityUpdate]] = Field(None, description="Activities of the updated sprint. Will delete or create activities if they are not present in one of the sprints")


class SprintResponse(SprintBase):
    """Schema for sprint response."""
    id: str = Field(..., description="Sprint ID")
    tasks: List[TaskResponse] = Field(..., default_factory=list, description="Tasks currently in sprint")
    duration: Optional[float] = Field(default=None, ge=0, description="Sprint duration in workdays")
    scoped: float = Field(..., description="Sum of story points of tasks in sprint")
    velocity: float = Field(..., description="Sum of story points of completed tasks in sprint")
    progress: float = Field(..., description="Average task progress in sprint")
    timeSpent: float = Field(..., description="Sum of time spent in tasks in sprint")
    otd: float = Field(..., description="Ratio of story points of completed tasks over total tasks in sprint")
    oqd: float = Field(..., description="Ratio of tasks completed correctly of total completed tasks in sprint")
    sprintTargets: List[Dict[str,str]] = Field(..., default_factory=dict, description="List of current and future sprints in project")
    transversalActivities: List[SprintTransversalActivityResponse] = Field(default_factory=list)
    taskStatuses: List[str] = Field(None, description="Existing task statuses")
    taskTypes: List[str] = Field(None, description="Existing task types")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class SprintListResponse(BaseModel):
    """Schema for sprint list response."""
    sprints: List[SprintResponse]
    total: int
    page: int
    size: int
    pages: int


class SprintLight(BaseModel):
    """Light schema for sprint response with only basic information."""
    id: str = Field(alias="_id", description="Sprint ID")
    projectId: str = Field(..., description="Sprint parent Project ID")
    sprintName: str = Field(..., description="Sprint name")
    status: str = Field(..., description="Sprint current status")
    startDate: str = Field(..., description="Sprint start date in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ")
    dueDate: str = Field(..., description="Sprint due date in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ")
    scoped: float = Field(..., description="Sum of task lengths in Sprint")
    capacity: float = Field(..., description="Sum of user availability in Sprint")
    velocity: float = Field(..., description="Sum of completed task lengths in Sprint")
    progress: float = Field(..., description="Average task progress in Sprint")
    timeSpent: float = Field(..., description="Sum of time spent in tasks in Sprint")
    otd: float = Field(..., description="Ratio of weighted completed tasks over total task lengths in Sprint")
    oqd: float = Field(..., description="Number of tasks done properly over number of tasks done in Sprint")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }


class SprintLightResponse(SprintBase):
    """Light schema for sprint response with only basic information."""
    id: str = Field(..., description="Sprint ID")
    scoped: float = Field(..., description="Sum of task lengths in Sprint")
    velocity: float = Field(..., description="Sum of completed task lengths in Sprint")
    progress: float = Field(..., description="Average task progress in Sprint")
    timeSpent: float = Field(..., description="Sum of time spent in tasks in Sprint")
    otd: float = Field(..., description="Ratio of weighted completed tasks over total task lengths in Sprint")
    oqd: float = Field(..., description="Number of tasks done properly over number of tasks done in Sprint")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }


class SprintListResponseLight(BaseModel):
    """Schema for sprint list response."""
    sprints: List[SprintLightResponse]
