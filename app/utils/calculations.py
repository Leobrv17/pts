"""
Correction des fonctions de calcul pour maintenir la compatibilité avec le code existant.
Ce fichier remplace app/utils/calculations.py
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from math import floor

from app.models.sprint import Sprint, SprintStatus, SprintTransversalActivity
from app.models.task import TaskStatus, TASKRFT, Task


async def calculate_sprint_metrics(sprint: Sprint, trans_acts: List[SprintTransversalActivity],
                                   tasks: List[Task]) -> Dict[str, float]:
    """
    Calcule les métriques du sprint selon les spécifications D-Req2.
    Maintient la compatibilité avec les noms de clés existants.
    """
    duration = calculate_weekdays(sprint.startDate, sprint.dueDate)

    if not tasks:
        return {
            "duration": duration,
            "scoped": 0.0,
            "velocity": 0.0,
            "progress": 0.0,  # Moyenne des progrès des tâches
            "time_spent": 0.0,
            "otd": 0.0,
            "oqd": 0.0,
            # Nouvelles métriques selon D-Req2
            "progress_sp": 0.0,  # Progression en Story Points
            "predictability": 0.0,  # Predictability %
            "rft": 0.0,  # RFT %
            "transversal_time": 0.0
        }

    # Calculs parallèles
    total_transversal_time, total_story_points, progress_sp, velocity, total_time_spent, rft, avg_progress = await asyncio.gather(
        calculate_transversal_time_in_days(trans_acts),
        calculate_story_points(tasks),
        calculate_progress_in_story_points(tasks),
        calculate_velocity(tasks, sprint.sprintName),
        calculate_total_time_in_days(tasks),
        calculate_rft_percentage(sprint.sprintName, sprint.status, tasks),
        calculate_average_progress(tasks)
    )

    # Predictability (OTD) - seulement si sprint Done
    predictability = 0.0
    otd = 0.0
    if sprint.status == SprintStatus.DONE and total_story_points > 0:
        predictability = (velocity / total_story_points) * 100
        otd = predictability  # Alias pour compatibilité

    return {
        # Clés existantes pour compatibilité
        "duration": round(duration, 1),
        "scoped": round(total_story_points, 1),
        "velocity": round(velocity, 1),
        "progress": round(avg_progress, 0),  # Progression moyenne des tâches
        "time_spent": round(total_time_spent + total_transversal_time, 1),
        "otd": round(otd, 0),
        "oqd": round(rft, 0),

        # Nouvelles métriques selon D-Req2
        "progress_sp": round(progress_sp, 1),  # Progression en Story Points
        "predictability": round(predictability, 0),  # Predictability %
        "rft": round(rft, 0),  # RFT %
        "transversal_time": round(total_transversal_time, 1)
    }


async def calculate_average_progress(tasks: List[Task]) -> float:
    """
    Calcule la progression moyenne pondérée par les Story Points.
    Maintient la compatibilité avec l'ancien système.
    """
    if not tasks:
        return 100.0

    sum_story_points = 0.0
    sum_progress = 0.0

    for task in tasks:
        if task.status != TaskStatus.CANCELLED:
            sum_story_points += task.storyPoints
            task_progress = task.progress if task.progress is not None else 0
            sum_progress += task.storyPoints * task_progress

    if sum_story_points == 0:
        return 100.0

    return sum_progress / sum_story_points


async def calculate_progress_in_story_points(tasks: List[Task]) -> float:
    """
    Calcule la progression en Story Points = somme des SPs multipliés par leur progression en %.
    Nouvelle métrique selon D-Req2.
    """
    if not tasks:
        return 0.0

    progress_sp = 0.0
    for task in tasks:
        if task.status != TaskStatus.CANCELLED:
            task_progress = task.progress if task.progress is not None else 0
            progress_sp += task.storyPoints * (task_progress / 100)

    return progress_sp


async def calculate_total_time_in_days(tasks: List[Task]) -> float:
    """
    Calcule le temps total passé en jours.
    """
    if not tasks:
        return 0.0

    total_time = 0.0
    for task in tasks:
        total_time += task.timeSpent if task.timeSpent else 0
    return total_time


async def calculate_transversal_time_in_days(activities: List[SprintTransversalActivity]) -> float:
    """
    Calcule le temps transversal en jours.
    """
    if not activities:
        return 0.0

    total_transversal_time = 0.0
    for activity in activities:
        total_transversal_time += activity.time_spent if activity.time_spent else 0
    return total_transversal_time


async def calculate_rft_percentage(sprint_name: str, status: SprintStatus, tasks: List[Task]) -> float:
    """
    Calcule le RFT (%) = nombre de RFT OK / nombre de Tasks avec Delivery Sprint = current sprint.
    Seulement calculé quand le Sprint est Done.
    """
    if status != SprintStatus.DONE or not tasks:
        return 0.0

    nb_rft_ok = 0.0
    nb_task_delivered = 0.0

    for task in tasks:
        if task.status == TaskStatus.DONE and is_delivery_sprint_current(task, sprint_name):
            nb_task_delivered += 1
            if task.rft == TASKRFT.OK:
                nb_rft_ok += 1

    if nb_task_delivered == 0:
        return 0.0

    return (nb_rft_ok / nb_task_delivered) * 100


async def calculate_task_metrics(task: Task, trans_tech_ratio: float) -> Dict[str, float]:
    """
    Calcule les métriques de tâche selon les spécifications D-Req2.
    """
    # Technical workload = Story Points / Ratio
    technical_workload = task.storyPoints / trans_tech_ratio if trans_tech_ratio > 0 else 0

    # Time spent en jours
    time_spent = task.timeSpent if task.timeSpent else 0

    # Updated = time_spent + remaining_time
    remaining_time = task.timeRemaining if task.timeRemaining else 0
    updated = time_spent + remaining_time

    # Delta = Technical load - updated
    delta = technical_workload - updated

    # Progress = time_spent / updated (en %)
    progress = 0.0
    if updated > 0:
        progress = (time_spent / updated) * 100

    return {
        "technical_load": round(technical_workload, 1),
        "time_spent": round(time_spent, 1),
        "updated": round(updated, 1),
        "delta": round(delta, 1),
        "progress": round(progress, 0)  # % sans décimale
    }


async def calculate_story_points(tasks: List[Task]) -> float:
    """
    Calcule la somme des story points dans une liste de tâches.
    """
    if not tasks:
        return 0.0

    total_story_points = 0.0
    for task in tasks:
        if task.status != TaskStatus.CANCELLED:  # Exclure les tâches annulées
            total_story_points += task.storyPoints

    return total_story_points


async def calculate_velocity(tasks: List[Task], sprint_name: str) -> float:
    """
    Calcule la vélocité = somme des SPs dont le statut est "Done".
    """
    if not tasks:
        return 0.0

    velocity = 0.0
    for task in tasks:
        if task.status == TaskStatus.DONE:
            velocity += task.storyPoints

    return velocity


def is_delivery_sprint_current(task: Task, sprint_name: str) -> bool:
    """
    Vérifie si le delivery sprint de la tâche correspond au sprint actuel.
    """
    return task.deliverySprint == sprint_name


def calculate_weekdays(start_date: datetime, due_date: datetime) -> int:
    """
    Calcule le nombre de jours ouvrables entre deux dates.
    """
    start = make_datetime_offset_naive(start_date)
    due = make_datetime_offset_naive(due_date)

    if start > due:
        start, due = due, start

    weekdays = 0
    current_date = start.date()

    while current_date <= due.date():  # Inclusif
        if current_date.weekday() < 5:  # Lundi=0, Vendredi=4
            weekdays += 1
        current_date += timedelta(days=1)

    return weekdays


def make_datetime_offset_naive(dt: datetime) -> datetime:
    """
    Convertit un datetime offset-aware en offset-naive (UTC).
    """
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# Fonctions pour maintenir la compatibilité avec le code existant
async def calculate_progress(tasks: List[Task]) -> float:
    """Alias pour la compatibilité - calcule le progrès moyen."""
    return await calculate_average_progress(tasks)


async def calculate_total_time(tasks: List[Task]) -> float:
    """Alias pour la compatibilité."""
    return await calculate_total_time_in_days(tasks)


async def calculate_transversal_time(activities: List[SprintTransversalActivity]) -> float:
    """Alias pour la compatibilité."""
    return await calculate_transversal_time_in_days(activities)


async def calculate_otd(status: SprintStatus, velocity: float, in_scope: float) -> float:
    """Alias pour la compatibilité - calcule la prédictibilité."""
    if status != SprintStatus.DONE or in_scope == 0:
        return 0.0
    return (velocity / in_scope) * 100


async def calculate_oqd(sprint_name: str, status: SprintStatus, tasks: List[Task]) -> float:
    """Alias pour la compatibilité - calcule le RFT."""
    return await calculate_rft_percentage(sprint_name, status, tasks)


def date_convertion(start_date: datetime, due_date: datetime) -> tuple:
    """
    Convert start and due dates to ISO 8601 string format.
    Fonction existante maintenue pour compatibilité.
    """
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    start = start_date.strftime(date_format)
    due = due_date.strftime(date_format)
    return start, due