"""Project service layer avec recalculs automatiques."""

from typing import List, Optional
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from app.models.project import Project, ProjectTransversalActivity
from app.models.task import Task
from app.schemas.project import ProjectUpdate, ProjectTransversalActivityCreate, ProjectBase
from app.utils.calculations import calculate_task_metrics


class ProjectService:
    """Service class for project operations avec recalculs automatiques."""

    _default_activities = [
        {"activity": "Ceremonies", "meaning": "SCRUM Meetings"},
        {"activity": "Project meetings", "meaning": "Other Meetings"},
        {"activity": "Estimations", "meaning": "Analysis, Questions/answers, Cost of production"},
        {"activity": "Deliveries", "meaning": "Preparation and test before sprint delivery and/or deployment"},
        {"activity": "Maintenance", "meaning": "Environment maintenance, configuration management"},
        {"activity": "Team management", "meaning": "Team organisation and project management / TL"},
        {"activity": "Capitalisation", "meaning": "Global project capitalisation"},
        {"activity": "Internal trainings", "meaning": "Team skills ramp-up"},
        {"activity": "Agency meetings", "meaning": "Meeting with HR, Business, medical appointment"},
        {"activity": "Lost Time", "meaning": "Example: dysfunctional accesses"},
    ]

    # Map schema fields to model fields
    _field_mapping = {
        'projectName': 'projectName',
        'technicalLoadRatio': 'transversal_vs_technical_workload_ratio',
        'centerId': 'centerId',
        'status': 'status',
        'taskStatuses': 'task_statuses',
        'taskTypes': 'task_types'
    }

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def _recalculate_project_tasks(self, project_id: ObjectId) -> bool:
        """Recalcule toutes les tâches du projet (quand le ratio change)."""
        try:
            # Récupérer le projet pour obtenir le nouveau ratio
            project = await self.engine.find_one(Project, Project.id == project_id)
            if not project:
                return False

            # Récupérer toutes les tâches du projet
            tasks = await self.engine.find(Task, (Task.projectId == project_id) & (Task.is_deleted == False))

            for task in tasks:
                # Recalculer les métriques avec le nouveau ratio
                metrics = await calculate_task_metrics(task, project.transversal_vs_technical_workload_ratio)

                # Mettre à jour les champs calculés
                old_technical_load = task.technicalLoad
                task.technicalLoad = metrics["technical_load"]
                task.delta = metrics["delta"]
                task.progress = metrics["progress"]

                # Si le technical load a changé et que timeRemaining était égal à l'ancien technical load,
                # on met à jour timeRemaining aussi
                if task.timeRemaining == old_technical_load:
                    task.timeRemaining = task.technicalLoad

                await self.engine.save(task)

            return True
        except Exception as e:
            print(f"Erreur lors du recalcul des tâches du projet {project_id}: {e}")
            return False

    async def create_project(self, project_data: ProjectBase) -> Project:
        """Create a new project."""
        project = Project(
            centerId=ObjectId(project_data.centerId) if project_data.centerId else None,
            projectName=project_data.projectName,
            status=project_data.status,
            sprints=[],
            users=[],
            transversal_vs_technical_workload_ratio=project_data.technicalLoadRatio,
            project_transversal_activities=[],
            task_statuses=project_data.taskStatuses,
            task_types=project_data.taskTypes,
        )

        try:
            await self.engine.save(project)
            return project
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating project: {str(e)}"
            )

    async def get_project_by_id(self, project_id: str, is_deleted: bool = False) -> Optional[Project]:
        """Get project by ID."""
        try:
            object_id = ObjectId(project_id)
            project = await self.engine.find_one(
                Project,
                (Project.id == object_id) & (Project.is_deleted == is_deleted)
            )
        except Exception as e:
            print(e)
            return None

        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found."
            )
        return project

    async def get_projects(
            self,
            skip: int = 0,
            limit: int = 100,
            center_id: Optional[str] = None,
            status: Optional[str] = None,
            is_deleted: bool = False
    ) -> tuple[List[Project], int]:
        """Get projects with pagination and filters."""
        query = Project.is_deleted == is_deleted

        if center_id:
            query = query & (Project.centerId == ObjectId(center_id))
        if status:
            query = query & (Project.status == status)

        projects = await self.engine.find(Project, query, skip=skip, limit=limit)
        total = await self.engine.count(Project, query)

        return projects, total

    async def update_project(self, project_update: ProjectUpdate) -> Optional[Project]:
        """Update project avec recalculs automatiques si le ratio change."""
        project = await self.get_project_by_id(project_update.id)
        update_data = project_update.model_dump(exclude_unset=True)

        # Sauvegarder l'ancien ratio pour détecter les changements
        old_ratio = project.transversal_vs_technical_workload_ratio

        if 'centerId' in update_data and update_data['centerId'] is not None:
            update_data['centerId'] = ObjectId(update_data.pop('centerId'))

        bad_fields = ["id", "transversalActivities"]
        for field, value in update_data.items():
            if field not in bad_fields:
                setattr(project, self._field_mapping[field], value)

        try:
            await self.engine.save(project)

            # Si le ratio a changé, recalculer toutes les tâches du projet
            if ('technicalLoadRatio' in update_data and
                project.transversal_vs_technical_workload_ratio != old_ratio):
                print(f"Ratio changé de {old_ratio} à {project.transversal_vs_technical_workload_ratio}, recalcul des tâches...")
                await self._recalculate_project_tasks(project.id)

            return project
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating project: {str(e)}"
            )

    async def delete_project(self, project_id: str) -> bool:
        """Soft delete project."""
        project = await self.get_project_by_id(project_id)

        project.is_deleted = True
        await self.engine.save(project)
        return True

    # Project Transversal Activity methods
    async def create_project_transversal_activity(
            self, activity_data: ProjectTransversalActivityCreate
    ) -> ProjectTransversalActivity:
        """Create a new project transversal activity."""
        project_id = ObjectId(activity_data.projectId)

        activity = ProjectTransversalActivity(
            project_id=project_id,
            activity=activity_data.activity,
            meaning=activity_data.meaning
        )

        try:
            await self.engine.save(activity)
            return activity
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating project transversal activity: {str(e)}"
            )

    async def create_default_transversal_activities(self, project_id: str):
        """Create default ProjectTransversalActivities for the given project."""
        for act in self._default_activities:
            await self.create_project_transversal_activity(ProjectTransversalActivityCreate(
                projectId=project_id,
                activity=act["activity"],
                meaning=act["meaning"]
            ))

    async def get_project_transversal_activity_by_id(self, activity_id: str, is_deleted: bool = False) -> Optional[ProjectTransversalActivity]:
        """Get project transversal activity by ID."""
        try:
            object_id = ObjectId(activity_id)
            activity = await self.engine.find_one(
                ProjectTransversalActivity,
                (ProjectTransversalActivity.id == object_id) & (ProjectTransversalActivity.is_deleted == is_deleted)
            )
        except Exception as e:
            print(e)
            return None

        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"ProjectTransversalActivity {activity_id} not found."
            )
        return activity

    async def get_project_transversal_activities_by_project(self, project_id: str, is_deleted: bool = False) -> List[ProjectTransversalActivity]:
        """Get project transversal activities by project ID."""
        try:
            project_object_id = ObjectId(project_id)
            return await self.engine.find(
                ProjectTransversalActivity,
                (ProjectTransversalActivity.project_id == project_object_id) & (
                            ProjectTransversalActivity.is_deleted == is_deleted)
            )
        except Exception as e:
            print(e)
            return []

    async def update_project_transversal_activity(
            self, activity_update: ProjectTransversalActivity
    ) -> Optional[ProjectTransversalActivity]:
        """Update project transversal activity."""
        activity = await self.get_project_transversal_activity_by_id(activity_update.id)
        update_data = activity_update.model_dump(exclude_unset=True)

        # Convert string ID to ObjectId
        if 'project_id' in update_data and update_data['project_id'] is not None:
            update_data['project_id'] = ObjectId(update_data['project_id'])

        for field, value in update_data.items():
            if field != 'id' and value is not None:
                setattr(activity, field, value)

        try:
            await self.engine.save(activity)
            return activity
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating project transversal activity: {str(e)}"
            )

    async def delete_project_transversal_activity(self, activity_id: str) -> bool:
        """Soft delete project transversal activity."""
        activity = await self.get_project_transversal_activity_by_id(activity_id)

        activity.is_deleted = True
        await self.engine.save(activity)
        return True