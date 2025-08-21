from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict

from bson import ObjectId
from odmantic import Model, Field


class ProjectStatus(str, Enum):
    BID = "BID"
    INPROGRESS = "In progress"
    DONE = "Done"
    CANCELLED = "Cancelled"
    CLOSED = "Closed"


class UserRole(str, Enum):
    DEVELOPER = "Developer"
    MANAGER = "Project Manager"
    TECH_LEAD = "Team Leader"
    ADMIN = "Admin"


class ProjectTransversalActivity(Model):
    """
    Schema for transversal activities.

    Attributes:
        project_id (ObjectId): A reference to the project this activity belongs to.
        activity (str): The name or description of the transversal activity.
        meaning (str): A detailed explanation or purpose of the activity.
        default (bool): Whether this activity is activated by default when creating a project.
        created_at (datetime): The timestamp indicating when the activity was created.
        is_deleted (bool): A flag indicating if the activity is marked as deleted.
    """
    project_id: ObjectId
    activity: str
    meaning: str = ""
    default: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False

    model_config = {"collection": "project_transversal_activity"}


class Project(Model):
    """
    Represents a project with associated details.

    Attributes:
        projectName (str): The name of the project.
        status (ProjectStatus): The current status of the project.
        roles (List[UserRole]): The roles involved in the project.
        sprints (List[ObjectId]): A list of sprints associated with the project.
        centerId (ObjectId): The ID of the service center the project is part of.
        users (List[ObjectId]): The IDs of the users working on this project and from its service center.
        created_at (datetime): The timestamp when the project was created.
        is_deleted (bool): A flag indicating if the project has been soft-deleted.
        transversal_vs_technical_workload_ratio: The ratio between technical activity and transversal activity times.
        project_transversal_activities (List[ObjectId]): The IDs corresponding to the transversal activities that can
            exist in this project.
        task_types (List[str]): A list of keys for every type that exists in this project.
        task_statuses (List[str]): A list of keys for every status that exists in this project.
    """
    projectName: str
    status: ProjectStatus
    roles: Optional[List[UserRole]] = None
    sprints: List[ObjectId] = Field(default_factory=list)
    centerId: Optional[ObjectId] = None
    users: List[ObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
    transversal_vs_technical_workload_ratio: float = 1.0
    project_transversal_activities: List[ObjectId] = Field(default_factory=list)
    possible_task_statuses: Optional[Dict[str,bool]] = Field(default_factory=dict)
    possible_task_types: Optional[Dict[str,bool]] = Field(default_factory=dict)
    task_types: Optional[List[str]] = Field(default_factory=list)
    task_statuses: Optional[List[str]] = Field(default_factory=list)

    model_config = {"collection": "project"}

