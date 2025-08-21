from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from bson import ObjectId
from odmantic import Model, Field
from pydantic import BaseModel
from pymongo import IndexModel, ASCENDING


class TaskStatus(str, Enum):
    OPEN = "Open"
    TODO = "To do"
    INVESTIGATION = "Under investigation"
    INPROGRESS = "In progress"
    INREVIEW = "In review"
    WAITING = "Waiting for customer"
    STANDBY = "Standby"
    DONE = "Done"
    CANCELLED = "Cancelled"
    POSTPONED = "Postponed"


class TaskType(str, Enum):
    BUG = "Bug"
    TASK = "Task"
    STORY = "Story"
    EPIC = "Epic"
    DOC = "Doc"
    TEST = "Test"
    DELIVERABLE = "Deliverable"


class TASKRFT(str, Enum):
    DEFAULT = ""
    OK = "OK"
    KO = "KO"


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
    SourceType.JIRA: {"Issue key": "key", "Issue Type": "type", "Summary": "summary", "Custom field (Story Points)": "storyPoints"},
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
        deliverySprint (str): The sprint associated with the delivery of the task.
        deliveryVersion (str): The version associated with the delivery of the task.
        type (TaskType): The type of task, either a bug or a general task.
        status (TaskStatus): The current status of the task.
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
    """
    sprintId: ObjectId
    projectId: ObjectId
    key: str
    summary: str
    storyPoints: float = Field(default=0.0)
    wu: str = Field(default="")
    comment: str = Field(default="")
    deliverySprint: Optional[str] = Field(default="")
    deliveryVersion: Optional[str] = Field(default="")
    type: TaskType = Field(default=TaskType.TASK)
    status: TaskStatus = Field(default=TaskStatus.TODO)
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

    model_config = {
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
        status (TaskStatus): The current status of the task.
        progress (str): The progress of the task.
        comment (str): Additional comments related to the task.
        deliverySprint (str): The sprint associated with the delivery of the task.
        deliveryVersion (str): The version associated with the delivery of the task.
        type (TaskType): The type of task, either a bug or a general task.
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
    status: TaskStatus
    progress: Optional[float]
    comment: Optional[str]
    deliverySprint: Optional[str]
    deliveryVersion: Optional[str]
    type: TaskType
    rft: TASKRFT
    assignee: Optional[List[ObjectId]]
    technicalLoad: float
    timeSpent: Optional[float]
    timeRemaining: Optional[float]
    delta: Optional[float]