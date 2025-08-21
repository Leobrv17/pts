from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from bson import ObjectId
from odmantic import Model, Field


class SprintStatus(str, Enum):
    TODO = "To do"
    INPROGRESS = "In progress"
    DONE = "Done"
    CLOSED = "Closed"


class SprintTransversalActivity(Model):
    """
    Schema for sprint-level transversal activities.

    Attributes:
        sprintId (ObjectId): The ID of the sprint associated with the transversal activities.
        activity (str): The name of the activity.
        meaning (str): A description of the activity.
        time_spent (float): The time spent on the activity so far.
        created_at (datetime): The timestamp indicating when the sprint transversal activities were created.
        is_deleted (bool): A flag indicating if the sprint transversal activities are marked as deleted. Defaults to `False`.
    """
    sprintId: ObjectId
    activity: str
    meaning: str = ""
    time_spent: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False

    model_config = {"collection": "sprint_transversal_activity"}


class Sprint(Model):
    """
    Represents a sprint associated with a project.

    Attributes:
        projectId (ObjectId): The ID of the project this sprint is part of.
        sprintName (str): The name of the sprint.
        status (SprintStatus): The current status of the sprint.
        startDate (datetime): The start date of the sprint.
        dueDate (datetime): The due date for the sprint's completion.
        capacity (float): The man*days available for this sprint.
        sprint_transversal_activities (List[ObjectId]): A list of references to the trans. activities of this sprint.
        task (List[ObjectId]): The IDs of tasks associated with the sprint.
        created_at (datetime): The timestamp when the sprint was created.
        is_deleted (bool): A flag indicating if the sprint has been soft-deleted.
        task_statuses (List[str]): The list of task statuses that can be selected in this sprint.
        task_types (List[str]): The list of task types that can be selected in this sprint.
    """
    projectId: ObjectId
    sprintName: str
    status: SprintStatus = SprintStatus.TODO
    startDate: datetime
    dueDate: datetime
    capacity: float
    sprint_transversal_activities: List[ObjectId] = Field(default_factory=list)
    task: List[ObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
    task_statuses: List[str] = Field(default_factory=list)
    task_types: List[str] = Field(default_factory=list)

    model_config = {"collection": "sprint"}