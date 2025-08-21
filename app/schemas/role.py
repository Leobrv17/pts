from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AccessLevelEnum(str, Enum):
    MANAGER = "PROJECT_MANAGER",
    LEADER = "TEAM_LEADER",
    MEMBER = "TEAM_MEMBER"


class DirectorAccess(BaseModel):
    id: Optional[str] = Field(..., description="Role ID.")
    serviceCenterId: str = Field(..., description="The ID of the service center attributed to that role.")
    serviceCenterName: str = Field(..., description="The name of the service center attributed to that role.")


class ProjectAccess(BaseModel):
    id: Optional[str] = Field(..., description="Role ID.")
    serviceCenterId: str = Field(..., description="The ID of the service center attributed to that role.")
    serviceCenterName: str = Field(..., description="The name of the service center attributed to that role.")
    projectId: str = Field(..., description="The ID of the project attributed to that role.")
    projectName: str = Field(..., description="The name of the project attributed to that role.")
    accessLevel: AccessLevelEnum = Field(..., description="The access level of that role.")
    occupancyRate: float = Field(..., description="How much time is spent by this user on this project.")
