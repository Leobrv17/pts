from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from bson import ObjectId
from odmantic import Model, Field
from pydantic import EmailStr


class UserTypeEnum(str, Enum):
    NORMAL = "NORMAL"
    SUPPORT = "SUPPORT"
    ADMIN = "ADMIN"


class AccessLevelEnum(str, Enum):
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TEAM_LEADER = "TEAM_LEADER"
    TEAM_MEMBER = "TEAM_MEMBER"
    GUEST = "GUEST"


class DirectorAccess(Model):
    """
    Represents director access to a service center.

    Attributes:
        user_id (ObjectId): The ID of the user with director access.
        service_center_id (ObjectId): The ID of the service center.
        service_center_name (str): The name of the service center.
        created_at (datetime): The timestamp when the access was created.
        is_deleted (bool): A flag indicating if the access has been soft-deleted.
    """
    user_id: ObjectId
    service_center_id: ObjectId
    service_center_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False

    model_config = {"collection": "director_access"}


class ProjectAccess(Model):
    """
    Represents project access for a user.

    Attributes:
        user_id (ObjectId): The ID of the user with project access.
        service_center_id (ObjectId): The ID of the service center.
        service_center_name (str): The name of the service center.
        project_id (ObjectId): The ID of the project.
        project_name (str): The name of the project.
        access_level (AccessLevelEnum): The access level for this project.
        occupancy_rate (float): The percentage of time spent on this project.
        created_at (datetime): The timestamp when the access was created.
        is_deleted (bool): A flag indicating if the access has been soft-deleted.
    """
    user_id: ObjectId
    service_center_id: ObjectId
    service_center_name: str
    project_id: ObjectId
    project_name: str
    access_level: AccessLevelEnum
    occupancy_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False

    model_config = {"collection": "project_access"}


class User(Model):
    """
    Represents a user in the system.

    Attributes:
        first_name (str): The first name of the user.
        family_name (str): The family name (last name) of the user.
        email (EmailStr): The email address of the user.
        type (UserTypeEnum): The type of user (NORMAL, SUPPORT, ADMIN).
        registration_number (str): The matricule/registration number of the user.
        trigram (str): The 3-letter trigram for the user.
        director_access_list (List[ObjectId]): List of director access IDs.
        project_access_list (List[ObjectId]): List of project access IDs.
        created_at (datetime): The timestamp when the user was created.
        is_deleted (bool): A flag indicating if the user has been soft-deleted.
    """
    first_name: str = Field(..., min_length=1, max_length=100)
    family_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    type: UserTypeEnum = Field(default=UserTypeEnum.NORMAL)
    registration_number: Optional[str] = Field(default="", max_length=50)
    trigram: str = Field(..., min_length=3, max_length=3)
    director_access_list: List[ObjectId] = Field(default_factory=list)
    project_access_list: List[ObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False

    model_config = {"collection": "user"}