from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict

from bson import ObjectId
from odmantic import Model, Field


class UserRole(str, Enum):
    DEVELOPER = "Developer"
    MANAGER = "Project Manager"
    TECH_LEAD = "Team Leader"
    ADMIN = "Admin"


class UserStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"


class User(Model):
    """
    Represents a user in the system.

    Attributes:
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        email (str): The email address of the user.
        role (UserRole): The role of the user within the system (e.g., Developer, Manager).
        status (UserStatus): The current status of the user (e.g., Active, Inactive).
        projects (List[ObjectId]): The IDs of the projects the user is in.
        project_percentages (Dict[str,float]): The percentage of time the user spends in each project.
        project_anonymity (Dict[str,bool]): Whether the user should use their trigram for display in each project.
        centers (List[ObjectId]): The list of IDs from service centers the user is in.
        created_at (datetime): The timestamp when the user was created.
        lastLogin (datetime, optional): The timestamp of the user's last login.
        is_deleted (bool): A flag indicating if the user has been soft-deleted.
    """
    first_name: str
    last_name: str
    email: Optional[str] = None
    role: UserRole
    status: UserStatus
    trigram: str = ""
    projects: List[ObjectId] = Field(default_factory=list)
    project_percentages: Dict[str, float] = Field(default_factory=dict)
    project_anonymity: Dict[str, bool] = Field(default_factory=dict)
    centers: List[ObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lastLogin: Optional[datetime] = None
    is_deleted: bool = False

    model_config = {"collection": "user"}