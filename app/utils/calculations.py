import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from math import floor

from app.models.sprint import Sprint, SprintStatus, SprintTransversalActivity
from app.models.task import TaskStatus, TASKRFT, Task


async def calculate_sprint_metrics(sprint: Sprint, trans_acts: List[SprintTransversalActivity],
                                   tasks: List[Task]) -> Dict[
    str, float]:
    """
    Helper function to calculate sprint metrics such as capacity, scoped, velocity, progress, and duration.

    Args:

        sprint (Sprint): The Sprint object for which the metrics are calculated.
        trans_acts (List[SprintTransversalActivity]): The list of transversal activities included in the sprint.
        tasks (List[Task]): The list of tasks included in the sprint.

    Returns:

        Dict[str, float]: A dictionary with calculated sprint metrics, including:
            - `scoped`: The total story points in the sprint. Rounded down to nearest integer.
            - `velocity`: The sum of story points for tasks whose status is "Done". Rounded down to nearest integer.
            - `progress`: The weighted progress based on the percentage progress * story points for each task.
                Rounded down to nearest integer.
            - `technical_time_spent`: The total time spent on technical tasks in the sprint.
                Ignored if no tasks are in the sprint.
            - `transversal_time_spent`: The total time spent on transversal tasks in the sprint.
                Ignored if no tasks are in the sprint.
            - `time_spent`: The total time spent on tasks in the sprint.
            - `duration`: The total number of weekdays in the sprint, based on start_date and due_date.
            - `otd`: The On-Time Delivery of the sprint, in percentage.
            - `oqd`: The On-Quality Delivery of the sprint, in percentage.
    """
    duration = calculate_weekdays(sprint.startDate, sprint.dueDate)

    if not tasks:
        return {
            "scoped": 0.0,
            "velocity": 0.0,
            "progress": 0.0,
            "time_spent": 0.0,
            "duration": duration,
            "otd": 0.0,
            "oqd": 0.0
        }

    total_transversal_time, total_story_points, overall_progress, velocity, total_time_spent, oqd = await asyncio.gather(
        calculate_transversal_time(trans_acts),
        calculate_story_points(tasks),
        calculate_progress(tasks),
        calculate_velocity(tasks, sprint.sprintName),
        calculate_total_time(tasks),
        calculate_oqd(sprint.sprintName, sprint.status, tasks)
    )

    overall_time_spent = total_time_spent + total_transversal_time
    otd = await calculate_otd(sprint.status, velocity, total_story_points)

    return {
        "scoped": round(total_story_points,1),
        "velocity": floor(velocity),
        "progress": floor(overall_progress),
        "technical_time_spent": round(total_time_spent,2),
        "transversal_time_spent": round(total_transversal_time,2),
        "time_spent": round(overall_time_spent,2),
        "duration": duration,
        "otd": floor(otd),
        "oqd": floor(oqd)
    }


async def calculate_story_points(tasks: List[Task]) -> int:
    """
    Calculates the sum of story points in a list of tasks.
    Args:

        tasks (List[Task]): The list of tasks the count the story points of.

    Returns:

        int: The sum of story points.
    """
    if tasks is None or len(tasks) < 1:
        return 0

    total_story_points = 0
    for task in tasks:
        total_story_points += task.storyPoints

    return total_story_points


async def calculate_progress(tasks: List[Task]) -> float:
    """
    Calculates the weighted average progress of a given list of tasks depending on each task's total story points.

    Args:

        tasks (List[Task]): The list of tasks to calculate the progress from.

    Returns:

        overall_progress (float): The weighted average progress of all the tasks in the list given as argument.
    """
    if tasks is None or len(tasks) < 1:
        return 100.0

    sum_story_points = 0.0
    sum_progress = 0.0

    for task in tasks:
        if task.status != TaskStatus.CANCELLED:
            sum_story_points += task.storyPoints
            sum_progress += task.storyPoints * (task.progress if task.progress is not None else 0)

    overall_progress = sum_progress / max(1,sum_story_points)

    return overall_progress


async def calculate_velocity(tasks: List[Task], sprint_name: str):
    """
    Calculates the velocity of a given sprint.

    Args:

        tasks (List[Task]): The tasks to check the completeness of.
        sprint_name (str): The name of the sprint the tasks in the list above are.

    Returns:

        The sum of story points for tasks given as argument, that are both done and to be delivered this sprint.
    """
    if tasks is None or len(tasks) < 1:
        return 0.0
    completed_story_points = 0.0

    for task in tasks:
        if task.status == TaskStatus.DONE and is_delivery_sprint_current(task, sprint_name):
            completed_story_points += task.storyPoints

    return completed_story_points


async def calculate_total_time(tasks: List[Task]):
    """
    Calculates the total time spent on a given list of tasks (usually the tasks from a sprint).

    Args:

        tasks (List[Task]): The list of tasks to calculate the time spent from.

    Returns:

        float: The sum of time spent on all the tasks in the list given as argument.
    """
    if not tasks:
        return 0.0

    total_time = 0.0
    for task in tasks:
        total_time += task.timeSpent
    return total_time


async def calculate_transversal_time(activities: List[SprintTransversalActivity]) -> float:
    """
    Calculates total transversal time in a list of transversal activities. Mainly used by calculate_sprint_metrics.

    Args:

        activities (List[SprintTransversalActivity]): The activities to sum the time from.

    Returns:

         float: The sum of the transversal times in the activities of the sprint given as argument.
            Defaults to 0.0 if no sprint can be found or the sprint is deleted.
    """
    if not activities:
        return 0.0

    total_transversal_time = 0.0
    for activity in activities:
        total_transversal_time += activity.time_spent
    return total_transversal_time


async def calculate_otd(status: SprintStatus, velocity: float, in_scope: float) -> float:
    """
    Calculates the On-Time Delivery (OTD) for a certain sprint, given its current metrics.
    Args:

        status: The sprint status. OTD is not calculated if sprint is not "Done".
        velocity: The sum of story points for tasks whose status is "Done".
        in_scope: The total amount of story points in the sprint.

    Returns:

        float: The percentage OTD of the sprint. Returns None if it can't be calculated.
    """
    if not (status == SprintStatus.DONE and in_scope):
        return 0.0

    return 100*velocity/in_scope


async def calculate_oqd(sprint_name: str, status: SprintStatus, tasks: List[Task]) -> float:
    """
    Calculates the On-Quality Delivery (OQD) of a sprint, given its tasks delivered.
    Args:

        sprint_name (str): The name of the current sprint.
        status (SprintStatus): The current status of the sprint.
        tasks (List[Task]): The tasks of the sprint.

    Returns:

        float: The percentage OQD of the sprint.
    """
    if not tasks:
        return 0.0
    if status != SprintStatus.DONE:
        return 0.0

    nb_rft_ok = 0.0
    nb_task_delivered = 0.0
    for task in tasks:
        if task.status == TaskStatus.DONE and is_delivery_sprint_current(task, sprint_name):
            nb_task_delivered += 1
            nb_rft_ok += (task.rft == TASKRFT.OK)

    if not nb_task_delivered:
        return 0.0
    return 100*nb_rft_ok/nb_task_delivered


async def calculate_task_metrics(task: Task, trans_tech_ratio: float) -> Dict[str, float]:
    """
    Calculates task-level metrics for a specific task, such as technical load, delta,
    updated time, and progress, using the sprint's ratio of technical to transversal workload.

    Args:

        task (Task): The task for which metrics are calculated.
        trans_tech_ratio (float): The ratio between transversal and technical activities in the project.

    Returns:

        Dict[str, float]: A dictionary containing task-level metrics:
            - `technical_load`: The technical load of the task.
            - `delta`: Difference between the technical load and the updated time.
            - `progress`: Percentage progress of the task.
    """
    updated_time = ((task.timeSpent if task.timeSpent is not None else 0)
                    + (task.timeRemaining if task.timeRemaining is not None else 0))

    if updated_time == 0.0:
        progress_percentage = 0
    else:
        progress_percentage = (task.timeSpent / updated_time) * 100

    technical_load = task.storyPoints / trans_tech_ratio
    delta = technical_load - updated_time

    return {
        "technical_load": round(technical_load, 2),
        "delta": round(delta, 2),
        "progress": int(progress_percentage)
    }


def is_delivery_sprint_current(task: Task, sprint_name: str) -> bool:
    """
    Checks if the delivery sprint of the task given as argument is the sprint the task is in.

    Args:

        task (Task): The task to check the delivery sprint of.
        sprint_name (str): The name of the sprint the task is in.

    Returns:

        bool: Whether the delivery sprint of the task given as argument is the sprint the task is in.
    """
    return task.deliverySprint == sprint_name


def date_convertion(start_date: datetime, due_date: datetime) -> tuple:
    """
    Convert start and due dates to ISO 8601 string format.

    This function takes two datetime objects (start_date and due_date) and converts them
    into strings formatted as ISO 8601 with microseconds precision.

    Args:

        start_date (datetime): The starting date to be converted.
        due_date (datetime): The due date to be converted.

    Returns:

        tuple: A tuple containing two strings:
            - The formatted start_date as a string.
            - The formatted due_date as a string.
    """
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    start = start_date.strftime(date_format)
    due = due_date.strftime(date_format)
    return start, due


def make_datetime_offset_naive(dt: datetime) -> datetime:
    """
    If a datetime is offset-aware, convert it to offset-naive (in the same UTC time).
    If it's already naive, return as-is.
    """
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def calculate_weekdays(start_date: datetime, due_date: datetime) -> int:
    """
    Calculate the number of weekdays between two dates, inclusive.

    Args:

        start_date (datetime): The starting date in ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.sss or YYYY-MM-DDTHH:MM:SS.sssZ)
        due_date (datetime): The ending date in ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.sss or YYYY-MM-DDTHH:MM:SS.sssZ)

    Returns:

        int: The number of weekdays between the two dates, including both start and end dates
    """
    start = make_datetime_offset_naive(start_date)
    due = make_datetime_offset_naive(due_date)

    if start > due:
        start, due = due, start

    weekdays = 0
    current_date = start.date()

    while current_date < due.date():
        if current_date.weekday() < 5:  # Monday is 0, Friday is 4
            weekdays += 1
        current_date += timedelta(days=1)

    return weekdays
