"""Task service layer avec calculs automatiques intégrés - CORRIGÉ."""

from typing import List, Optional
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from app.models.task import Task, TASKRFT, TaskStatus, TaskType
from app.models.project import Project
from app.models.sprint import Sprint
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.calculations import calculate_task_metrics


class TaskService:
    """Service class for task operations avec calculs automatiques."""

    # Map schema fields to model fields
    _field_mapping = {
        'sprintId': 'sprintId',
        'projectId': 'projectId',
        'key': 'key',
        'summary': 'summary',
        'storyPoints': 'storyPoints',
        'wu': 'wu',
        'comment': 'comment',
        'deliverySprint': 'deliverySprint',
        'deliveryVersion': 'deliveryVersion',
        'type': 'type',
        'status': 'status',
        'rft': 'rft',
        'technicalLoad': 'technicalLoad',
        'timeSpent': 'timeSpent',
        'timeRemaining': 'timeRemaining',
        'progress': 'progress',
        'assignee': 'assignee',
        'delta': 'delta'
    }

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    def _validate_and_convert_status(self, status_id: str) -> TaskStatus:
        """Validate and convert status ID to TaskStatus enum."""
        try:
            return TaskStatus(status_id)
        except ValueError:
            valid_statuses = [status.value for status in TaskStatus]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task status '{status_id}'. Valid statuses: {valid_statuses}"
            )

    def _validate_and_convert_type(self, type_id: str) -> TaskType:
        """Validate and convert type ID to TaskType enum."""
        try:
            return TaskType(type_id)
        except ValueError:
            valid_types = [task_type.value for task_type in TaskType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task type '{type_id}'. Valid types: {valid_types}"
            )

    def _validate_and_convert_rft(self, rft_id: str) -> TASKRFT:
        """Validate and convert RFT ID to TASKRFT enum."""
        try:
            return TASKRFT(rft_id)
        except ValueError:
            valid_rfts = [rft.value for rft in TASKRFT]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid RFT value '{rft_id}'. Valid values: {valid_rfts}"
            )

    async def _calculate_and_update_fields(self, task: Task, initialize_time_remaining: bool = False) -> Task:
        """Calcule et met à jour les champs automatiques de la tâche."""
        # Récupérer le projet pour obtenir le ratio
        project = await self.engine.find_one(Project, Project.id == task.projectId)
        if not project:
            return task

        # Calculer les métriques
        metrics = await calculate_task_metrics(task, project.transversal_vs_technical_workload_ratio)

        # Mettre à jour les champs calculés
        task.technicalLoad = metrics["technical_load"]
        task.delta = metrics["delta"]
        task.progress = metrics["progress"]

        # Initialiser timeRemaining seulement si explicitement demandé ou si c'est None
        if initialize_time_remaining or task.timeRemaining is None:
            task.timeRemaining = task.technicalLoad

        # Gestion automatique du Delivery Sprint
        if task.status == TaskStatus.DONE and not task.deliverySprint:
            sprint = await self.engine.find_one(Sprint, Sprint.id == task.sprintId)
            if sprint:
                task.deliverySprint = sprint.sprintName

        return task

    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task avec calculs automatiques."""
        # Convert string IDs to ObjectIds
        sprint_oid = ObjectId(task_data.sprintId)
        project_oid = ObjectId(task_data.projectId)
        assignees = [ObjectId(aid) for aid in task_data.assignee] if task_data.assignee else []

        # Validate and convert enums
        task_status = self._validate_and_convert_status(task_data.status)
        task_type = self._validate_and_convert_type(task_data.type)

        task = Task(
            sprintId=sprint_oid,
            projectId=project_oid,
            key=task_data.key,
            summary=task_data.summary,
            storyPoints=task_data.storyPoints if task_data.storyPoints else 0,
            wu="",
            comment="",
            deliverySprint="",
            deliveryVersion="",
            type=task_type,
            status=task_status,
            rft=TASKRFT.DEFAULT,
            technicalLoad=0,
            timeSpent=0,
            timeRemaining=None,  # Will be initialized in _calculate_and_update_fields
            progress=0,
            assignee=assignees,
            delta=0
        )

        # Calculer les champs automatiques et initialiser timeRemaining
        task = await self._calculate_and_update_fields(task, initialize_time_remaining=True)

        try:
            await self.engine.save(task)
            return task
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating task: {str(e)}"
            )

    async def get_task_by_id(self, task_id: str, is_deleted: bool = False) -> Optional[Task]:
        """Get task by ID."""
        try:
            object_id = ObjectId(task_id)
            task = await self.engine.find_one(
                Task,
                (Task.id == object_id) & (Task.is_deleted == is_deleted)
            )
        except Exception as e:
            print(str(e))
            return None

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found."
            )
        return task

    async def update_task(self, task_update: TaskUpdate) -> Optional[Task]:
        """Update task avec recalculs automatiques."""
        task = await self.get_task_by_id(task_update.id)
        if not task:
            return None

        update_data = task_update.model_dump(exclude_unset=True)

        # Sauvegarder les anciennes valeurs pour détecter les changements
        old_story_points = task.storyPoints
        old_time_remaining = task.timeRemaining

        # Déterminer si timeRemaining a été explicitement fourni dans l'update
        time_remaining_explicitly_set = 'timeRemaining' in update_data

        # Convert string IDs to ObjectIds
        if 'sprintId' in update_data and update_data['sprintId'] is not None:
            update_data['sprintId'] = ObjectId(update_data['sprintId'])
        if 'projectId' in update_data and update_data['projectId'] is not None:
            update_data['projectId'] = ObjectId(update_data['projectId'])
        if 'assignee' in update_data and update_data['assignee'] is not None:
            update_data['assignee'] = [ObjectId(aid) for aid in update_data['assignee']]

        # Validate and convert enums
        if 'status' in update_data and update_data['status'] is not None:
            update_data['status'] = self._validate_and_convert_status(update_data['status'])
        if 'type' in update_data and update_data['type'] is not None:
            update_data['type'] = self._validate_and_convert_type(update_data['type'])
        if 'rft' in update_data and update_data['rft'] is not None:
            update_data['rft'] = self._validate_and_convert_rft(update_data['rft'])

        # Mettre à jour les champs
        for field, value in update_data.items():
            if field != 'id':
                setattr(task, self._field_mapping[field], value)

        # Réinitialiser timeRemaining seulement si :
        # 1. storyPoints a changé ET timeRemaining n'a pas été explicitement fourni
        # 2. OU si c'est la première fois qu'on met timeRemaining (était None)
        should_reinitialize_time_remaining = False

        if 'storyPoints' in update_data and task.storyPoints != old_story_points:
            if not time_remaining_explicitly_set:
                # storyPoints a changé mais timeRemaining n'est pas explicitement fourni
                # On réinitialise seulement si l'ancienne valeur était égale au technical load
                project = await self.engine.find_one(Project, Project.id == task.projectId)
                if project:
                    old_technical_load = old_story_points / project.transversal_vs_technical_workload_ratio
                    if old_time_remaining == old_technical_load:
                        should_reinitialize_time_remaining = True

        # Si timeRemaining était None et n'a pas été explicitement fourni, l'initialiser
        if task.timeRemaining is None and not time_remaining_explicitly_set:
            should_reinitialize_time_remaining = True

        # Calculer les champs automatiques
        task = await self._calculate_and_update_fields(task, initialize_time_remaining=should_reinitialize_time_remaining)

        try:
            await self.engine.save(task)
            return task
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating task: {str(e)}"
            )

    async def delete_task(self, task_id: str) -> bool:
        """Soft delete task."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False

        task.is_deleted = True
        await self.engine.save(task)
        return True

    async def get_tasks_by_sprint(self, sprint_id: str, is_deleted: bool = False) -> List[Task]:
        """Get tasks by sprint ID."""
        try:
            sprint_object_id = ObjectId(sprint_id)
            return await self.engine.find(
                Task,
                (Task.sprintId == sprint_object_id) & (Task.is_deleted == is_deleted)
            )
        except Exception as e:
            print(e)
            return []

    async def get_task_type_list(self) -> dict:
        """Get all existing task types with their IDs."""
        return {
            "BUG": "Bug",
            "TASK": "Task",
            "STORY": "Story",
            "EPIC": "Epic",
            "DOC": "Doc",
            "TEST": "Test",
            "DELIVERABLE": "Deliverable"
        }

    async def get_task_status_list(self) -> dict:
        """Get all existing task statuses with their IDs."""
        return {
            "OPEN": "Open",
            "TODO": "To do",
            "INVEST": "Under investigation",
            "PROG": "In progress",
            "REV": "In review",
            "CUST": "Waiting for customer",
            "STANDBY": "Standby",
            "DONE": "Done",
            "CANCEL": "Cancelled",
            "POST": "Postponed"
        }