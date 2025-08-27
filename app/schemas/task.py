"""Task schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class TaskBase(BaseModel):
    """Base task schema."""
    sprintId: str = Field(..., description="Sprint ID")
    projectId: str = Field(..., description="Project ID")
    type: str = Field(default="TASK", description="Task type ID (BUG, TASK, STORY, etc.)")
    key: str = Field(..., min_length=1, max_length=10000, description="Task key")
    summary: str = Field(..., min_length=0, description="Task summary")
    storyPoints: float = Field(default=0.0, ge=0, description="Story points")
    wu: str = Field(default="", description="Work units")
    status: str = Field(default="TODO", description="Task status ID (OPEN, TODO, PROG, etc.)")
    progress: Optional[float] = Field(default=None, ge=0, le=100, description="Progress percentage")
    comment: str = Field(default="", description="Comments")
    deliverySprint: Optional[str] = Field(default="", description="Delivery sprint")
    deliveryVersion: Optional[str] = Field(default="", description="Delivery version")
    rft: str = Field(default="", description="Ready for test (OK, KO, or empty)")
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
    type: str = Field(default="TASK", description="Task type ID: TASK, EPIC, BUG, STORY, DOC, TEST, DELIVERABLE")
    key: str = Field(..., min_length=0, max_length=10000, description="Task key")
    summary: str = Field(..., min_length=1, description="Task summary")
    storyPoints: Optional[float] = Field(default=0.0, ge=0, description="Story points")
    status: str = Field(default="TODO", description="Task status ID: OPEN, TODO, INVEST, PROG, REV, CUST, STANDBY, DONE, CANCEL, POST")
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
    type: Optional[str] = Field(None, description="Task type ID")
    status: Optional[str] = Field(None, description="Task status ID")
    rft: Optional[str] = Field(None, description="Ready for test")
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
    """Schema for any task type or status."""
    key: str = Field(..., description="The enum ID (e.g., 'BUG', 'OPEN')")
    specific: str = Field(..., description="The human-readable label (e.g., 'Bug', 'Open')")


class TaskSpecificsResponse(BaseModel):
    """Schema for task type/status response."""
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