"""Task schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models.task import TaskStatus, TaskType, TASKRFT


class TaskBase(BaseModel):
    """Base task schema."""
    sprintId: str = Field(..., description="Sprint ID")
    projectId: str = Field(..., description="Project ID")
    type: TaskType = Field(default=TaskType.TASK, description="Task type")
    key: str = Field(..., min_length=1, max_length=10000, description="Task key")
    summary: str = Field(..., min_length=1, description="Task summary")
    storyPoints: float = Field(default=0.0, ge=0, description="Story points")
    wu: str = Field(default="", description="Work units")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Task status")
    progress: Optional[float] = Field(default=None, ge=0, le=100, description="Progress percentage")
    comment: str = Field(default="", description="Comments")
    deliverySprint: Optional[str] = Field(default="", description="Delivery sprint")
    deliveryVersion: Optional[str] = Field(default="", description="Delivery version")
    rft: TASKRFT = Field(default=TASKRFT.DEFAULT, description="Ready for test")
    assignee: Optional[List[str]] = Field(default_factory=list, description="Assignee user IDs")
    technicalLoad: Optional[float] = Field(default=0.0, ge=0, description="Technical load")
    timeSpent: Optional[float] = Field(default=0.0, ge=0, description="Time spent")
    timeRemaining: Optional[float] = Field(default=None, ge=0, description="Time remaining")
    delta: Optional[float] = Field(default=None, description="Delta between estimated and actual")


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    id: Optional[str] = Field(None, description="Task ID")
    sprintId: str = Field(..., description="Parent sprint ID")
    projectId: str = Field(..., description="Parent project ID")
    type: TaskType = Field(default=TaskType.TASK, description="Task type: e.g. TASK, EPIC, BUG...")
    key: str = Field(..., min_length=0, max_length=10000, description="Task key")
    summary: str = Field(..., min_length=1, description="Task summary")
    storyPoints: Optional[float] = Field(default=0.0, ge=0, description="Story points")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Task status")
    assignee: Optional[List[str]] = Field(default_factory=list, description="Task assignees. List of User IDs")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    id: str = Field(..., description="Task ID")
    sprintId: Optional[str] = None
    projectId: Optional[str] = None
    key: Optional[str] = Field(None, min_length=1, max_length=10000)
    summary: Optional[str] = Field(None, min_length=1)
    storyPoints: Optional[float] = Field(None, ge=0)
    wu: Optional[str] = None
    comment: Optional[str] = None
    deliverySprint: Optional[str] = None
    deliveryVersion: Optional[str] = None
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    rft: Optional[TASKRFT] = None
    technicalLoad: Optional[float] = Field(None, ge=0)
    timeSpent: Optional[float] = Field(None, ge=0)
    timeRemaining: Optional[float] = Field(None, ge=0)
    progress: Optional[float] = Field(None, ge=0, le=100)
    assignee: Optional[List[str]] = None
    delta: Optional[float] = None


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: str = Field(..., description="Task ID")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class HttpResponseTaskList(BaseModel):
    """Schema for partial task list response."""
    sprintId: str
    taskList: List[TaskResponse]


class HttpResponseTaskListResponse(BaseModel):
    """Schema for task list full response with pagination."""
    responseList: List[HttpResponseTaskList]
    total: int
    page: int
    size: int
    pages: int


class HttpResponseDeleteStatus(BaseModel):
    """Schema for delete status response."""
    status: bool
    msg: str


class TaskSpecifics(BaseModel):
    """Schema for any task type."""
    key: str
    specific: str


class TaskSpecificsResponse(BaseModel):
    """Schema for task type response."""
    specifics: List[TaskSpecifics]


class TaskImportResponse(BaseModel):
    """Schema for task import response."""
    message: str
    importedCount: int
    totalTasksInDb: int
    duplicateCount: int
    duplicateKeys: List[str]
    skippedRows: int
    skippedRowNumbers: List[int] = []
