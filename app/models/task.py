from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from bson import ObjectId
from odmantic import Model, Field
from pydantic import BaseModel
from pymongo import IndexModel, ASCENDING


class TaskStatus(str, Enum):
    OPEN = "OPEN"
    TODO = "TODO"
    INVESTIGATION = "INVEST"
    INPROGRESS = "PROG"
    INREVIEW = "REV"
    WAITING = "CUST"
    STANDBY = "STANDBY"
    DONE = "DONE"
    CANCELLED = "CANCEL"
    POSTPONED = "POST"


class TaskType(str, Enum):
    BUG = "BUG"
    TASK = "TASK"
    STORY = "STORY"
    EPIC = "EPIC"
    DOC = "DOC"
    TEST = "TEST"
    DELIVERABLE = "DELIVERABLE"


class TASKRFT(str, Enum):
    DEFAULT = ""
    OK = "OK"
    KO = "KO"


class TaskDeliveryStatus(str, Enum):
    """Enum pour le statut de livraison de la tâche."""
    DEFAULT = ""  # Null/vide
    OK = "OK"     # Livrée avec succès
    KO = "KO"     # Problème de livraison


# Enum for source selection (for CSV import)
class SourceType(str, Enum):
    JIRA = "jira"
    GITLAB = "gitlab"


class ImportCSVResponse(BaseModel):
    status: bool
    msg: str


# Predefined column mappings for CSV import
EXPECTED_HEADERS = {
    SourceType.JIRA: ["Issue key", "Issue Type", "Summary", "Custom field (Story Points)"],
    SourceType.GITLAB: ["Issue ID", "Title", "Assignee"]
}

DB_FIELD_MAPPING = {
    SourceType.JIRA: {"Issue key": "key", "Issue Type": "type", "Summary": "summary",
                      "Custom field (Story Points)": "storyPoints"},
    SourceType.GITLAB: {"Issue ID": "key", "Title": "summary", "Assignee": "assignee"}
}


class Task(Model):
    """
    Represents a task associated with a sprint and project.

    Attributes:
        sprintId (ObjectId): The ID of the sprint this task belongs to.
        projectId (ObjectId): The ID of the project this task is part of.
        key (str): A unique key or identifier for the task.
        summary (str): A brief summary of the task.
        storyPoints (float): The estimated effort required for the task.
        wu (str): Work units associated with the task.
        comment (str): Additional comments related to the task.
        deliveryStatus (TaskDeliveryStatus): The delivery status of the task (OK/KO/Default).
        deliveryVersion (str): The version associated with the delivery of the task.
        type (TaskType): The type of task, stores the enum ID (BUG, TASK, etc.).
        status (TaskStatus): The current status of the task, stores the enum ID (OPEN, TODO, etc.).
        rft (TASKRFT): Readiness for task completion.
        technicalLoad (float): The technical load associated with the task.
        timeSpent (float): The amount of effort consumed so far.
        timeRemaining (float): The remaining effort required to complete the task.
        progress (str): The progress of the task.
        assignee (List[ObjectId]): The list of users assigned to the task. Should usually be one.
        delta (float): The difference between estimated and actual effort.
        ticketLink (str): A link to the associated ticket or issue.
        description (str): A detailed description of the task.
        created_at (datetime): The timestamp when the task was created.
        is_deleted (bool): A flag indicating if the task has been soft-deleted.
        is_cascade_deleted (bool): A flag indicating if the task was deleted due to cascade deletion. Defaults to `False`.
    """
    sprintId: ObjectId
    projectId: ObjectId
    key: str
    summary: str
    storyPoints: float = Field(default=0.0)
    wu: str = Field(default="")
    comment: str = Field(default="")
    deliveryStatus: TaskDeliveryStatus = Field(default=TaskDeliveryStatus.DEFAULT)  # Remplace deliverySprint
    deliveryVersion: Optional[str] = Field(default="")
    type: TaskType = Field(default=TaskType.TASK)  # Stores "TASK", "BUG", etc.
    status: TaskStatus = Field(default=TaskStatus.TODO)  # Stores "TODO", "PROG", etc.
    rft: TASKRFT = Field(default=TASKRFT.DEFAULT)
    technicalLoad: Optional[float] = Field(default=0.0)
    timeSpent: Optional[float] = Field(default=0.0)
    timeRemaining: Optional[float] = Field(default=None)
    progress: Optional[float] = Field(default=None)
    assignee: Optional[List[ObjectId]] = Field(default_factory=list)
    delta: Optional[float] = Field(default=None)
    ticketLink: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = Field(default=False)
    is_cascade_deleted: bool = Field(default=False)

    model_config = {
        "collection": "task",
        "indexes": lambda: [IndexModel([("id", ASCENDING), ("is_deleted", ASCENDING)])]
    }


class TaskMandatoryFields(Model):
    """
    Represents the mandatory fields for a task.

    Attributes:
        sprintId (ObjectId): The ID of the sprint this task belongs to.
        projectId (ObjectId): The ID of the project this task is part of.
        key (str): A unique key or identifier for the task.
        summary (str): A brief summary of the task.
        storyPoints (float): The estimated effort required for the task.
        wu (str): Work units associated with the task.
        status (TaskStatus): The current status of the task, stores the enum ID.
        progress (str): The progress of the task.
        comment (str): Additional comments related to the task.
        deliveryStatus (TaskDeliveryStatus): The delivery status of the task.
        deliveryVersion (str): The version associated with the delivery of the task.
        type (TaskType): The type of task, stores the enum ID.
        rft (TASKRFT): Readiness for task completion.
        assignee (List[ObjectId]): List of users assigned to the task.
        technicalLoad (float): The technical load associated with the task.
        timeSpent (float): The amount of effort consumed so far.
        timeRemaining (float): The remaining effort required to complete the task.
        delta (float): The difference between estimated and actual effort.
    """
    sprintId: ObjectId
    projectId: ObjectId
    key: str
    summary: str
    storyPoints: float
    wu: str
    status: TaskStatus  # Stores enum ID
    progress: Optional[float]
    comment: Optional[str]
    deliveryStatus: TaskDeliveryStatus  # Remplace deliverySprint
    deliveryVersion: Optional[str]
    type: TaskType  # Stores enum ID
    rft: TASKRFT
    assignee: Optional[List[ObjectId]]
    technicalLoad: float
    timeSpent: Optional[float]
    timeRemaining: Optional[float]
    delta: Optional[float]