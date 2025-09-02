from pydantic import BaseModel
from typing import List, Optional


class HttpResponseDeleteStatus(BaseModel):
    """General schema for deletion status."""
    status: bool
    msg: str


class CascadeDeletionResponse(BaseModel):
    """Schema for cascade deletion response."""
    status: bool
    msg: str
    deleted_elements: dict


class CascadeDeletedElementsResponse(BaseModel):
    """Schema for cascade deleted elements response."""
    sprints: List[str] = []
    tasks: List[str] = []
    sprint_transversal_activities: List[str] = []


class DeletedElementsStatusResponse(BaseModel):
    """Schema for deleted elements status with cascade information."""
    element_id: str
    element_type: str  # "project", "sprint", "task", "sprint_transversal_activity"
    is_deleted: bool
    is_cascade_deleted: bool
    deleted_at: Optional[str] = None
    parent_element_id: Optional[str] = None  # ID de l'élément parent qui a causé la suppression en cascade