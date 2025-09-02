from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional

from bson import ObjectId
from odmantic import Model, Field
from pydantic import EmailStr


class ServiceCenterStatus(str, Enum):
    OPERATIONAL = "Operational"
    CLOSED = "Closed"


class ServiceCenter(Model):
    """
    Represents a service center with associated details.

    Attributes:
        centerName (str): The name of the service center.
        location (str): The physical location of the service center.
        contactEmail (str): The contact email address for the service center.
        contactPhone (str): The contact phone number for the service center.
        status (ServiceCenterStatus): The current status of the service center, operational or closed.
        projects (List[ObjectId]): A list of project IDs associated with the service center.
        users (List[ObjectId]): A list of user IDs associated with the service center.
        created_at (datetime): The timestamp when the service center was created.
        is_deleted (bool): A flag indicating if the service center has been soft-deleted.
        is_cascade_deleted (bool): A flag indicating if the service center was deleted due to cascade deletion. Defaults to `False`.
        transversal_activities (List[Dict[str,str]]): The default transversal activities that will be set
            for any project in this service center.
        possible_task_statuses (Dict[str,bool]): A list of tick boxes for every status that exists (or not) for a task.
        possible_task_types (Dict[str,bool]): A list of tick boxes for every type that exists (or not) for a task.
    """
    centerName: str
    location: str = ""
    contactEmail: Optional[str] = None
    contactPhone: str = ""
    status: ServiceCenterStatus = ServiceCenterStatus.OPERATIONAL
    projects: List[ObjectId] = Field(default_factory=list)
    users: List[ObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
    is_cascade_deleted: bool = False
    transversal_activities: List[Dict[str,str]] = Field(default_factory=list)
    possible_task_statuses: Dict[str, bool] = Field(default_factory=dict)
    possible_task_types: Dict[str,bool] = Field(default_factory=dict)

    model_config = {"collection": "service_center"}