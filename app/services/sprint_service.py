"""Sprint service layer."""
from datetime import datetime, timezone
from typing import List, Optional, Dict
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from app.models.sprint import Sprint, SprintTransversalActivity, SprintStatus
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintTransversalActivityUpdate


class SprintService:
    """Service class for sprint operations."""

    # Map schema fields to model fields
    _field_mapping = {
        'projectId': 'projectId',
        'sprintName': 'sprintName',
        'status': 'status',
        'startDate': 'startDate',
        'dueDate': 'dueDate',
        'capacity': 'capacity',
        'duration': 'duration',
        'sprintTransversalActivities': 'sprint_transversal_activities',
        'taskIds': 'task',
        'taskStatuses': 'task_statuses',
        'taskTypes': 'task_types'
    }

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def create_sprint(self, sprint_data: SprintCreate) -> Sprint:
        """Create a new sprint."""
        # Convert string IDs to ObjectIds
        project_id = ObjectId(sprint_data.projectId)

        sprint = Sprint(
            projectId=project_id,
            sprintName=sprint_data.sprintName,
            status=sprint_data.status,
            startDate=sprint_data.startDate,
            dueDate=sprint_data.dueDate,
            capacity=sprint_data.capacity,
            sprint_transversal_activities=[],
            task=[],
            task_statuses=[],
            task_types=[],
        )

        try:
            await self.engine.save(sprint)
            return sprint
        except Exception as e: # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating sprint: {str(e)}"
            )

    async def get_sprint_by_id(self, sprint_id: str, is_deleted: bool = False) -> Optional[Sprint]:
        """Get sprint by ID."""
        try:
            object_id = ObjectId(sprint_id)
            sprint = await self.engine.find_one(
                Sprint,
                (Sprint.id == object_id) & (Sprint.is_deleted == is_deleted)
            )
        except Exception as e: # pragma: no cover
            print(str(e))
            return None

        if not sprint:
            raise HTTPException(
                status_code=404,
                detail=f"Sprint {sprint_id} not found."
            )
        return sprint

    async def get_sprints(
        self,
        skip: int = 0,
        limit: int = 100,
        sprint_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        is_deleted: bool = False
    ) -> tuple[List[Sprint], int]:
        """Get sprints with pagination and filters."""
        query = Sprint.is_deleted == is_deleted

        if sprint_ids:
            sprint_oids = [ObjectId(sid) for sid in sprint_ids]
            query = query & (Sprint.id.in_(sprint_oids))
        if project_id:
            query = query & (Sprint.projectId == ObjectId(project_id))
        if status:
            query = query & (Sprint.status == status)

        sprints = await self.engine.find(Sprint, query, skip=skip, limit=limit)

        return sprints, len(sprints)

    async def update_sprint(self, sprint_update: SprintUpdate) -> Optional[Sprint]:
        """Update sprint."""
        sprint = await self.get_sprint_by_id(sprint_update.id)
        update_data = sprint_update.model_dump(exclude_unset=True)

        if 'projectId' in update_data and update_data['projectId'] is not None:
            update_data['projectId'] = ObjectId(update_data.pop('projectId'))

        bad_fields = ['id', 'transversalActivities']
        for field, value in update_data.items():
            if field not in bad_fields:
                setattr(sprint, self._field_mapping[field], value)

        try:
            await self.engine.save(sprint)
            return sprint
        except Exception as e: # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating sprint: {str(e)}"
            )

    async def delete_sprint(self, sprint_id: str) -> bool:
        """Soft delete sprint."""
        sprint = await self.get_sprint_by_id(sprint_id)

        sprint.is_deleted = True
        await self.engine.save(sprint)
        return True

    async def get_relevant_sprints_by_project(self, project_id: str) -> List[Dict[str,str]]:
        """Get current and future sprints for this project."""
        try:
            project_oid = ObjectId(project_id)
        except Exception as e: # pragma: no cover
            print(e)
            return []

        sprints = await self.engine.find(Sprint, (Sprint.projectId == project_oid) & (Sprint.is_deleted == False)
                                         & (Sprint.status != SprintStatus.CLOSED) & (Sprint.dueDate > datetime.now(timezone.utc)))

        relevant_sprint_response = []
        for sprint in sprints:
            relevant_sprint_response.append({"id": str(sprint.id), "name":sprint.sprintName})

        return relevant_sprint_response

    # Sprint Transversal Activity methods
    async def create_sprint_transversal_activity(
        self, activity: SprintTransversalActivity
    ) -> SprintTransversalActivity:
        """Create a new sprint transversal activity."""
        try:
            await self.engine.save(activity)
            return activity
        except Exception as e: # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating sprint transversal activity: {str(e)}"
            )

    async def get_sprint_transversal_activity_by_id(self, activity_id: str, is_deleted: bool = False) -> Optional[SprintTransversalActivity]:
        """Get sprint transversal activity by ID."""
        try:
            object_id = ObjectId(activity_id)
            activity = await self.engine.find_one(
                SprintTransversalActivity,
                (SprintTransversalActivity.id == object_id) & (SprintTransversalActivity.is_deleted == is_deleted)
            )
        except Exception as e:  # pragma: no cover
            print(e)
            return None

        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"SprintTransversalActivity {activity_id} not found."
            )
        return activity

    async def get_sprint_transversal_activities_by_sprint(self, sprint_id: str, is_deleted: bool = False) -> List[SprintTransversalActivity]:
        """Get sprint transversal activities by sprint ID."""
        try:
            sprint_object_id = ObjectId(sprint_id)
            return await self.engine.find(
                SprintTransversalActivity,
                (SprintTransversalActivity.sprintId == sprint_object_id) & (SprintTransversalActivity.is_deleted == is_deleted)
            )
        except Exception as e:  # pragma: no cover
            print(e)
            return []

    async def update_sprint_transversal_activity(
        self, activity_update: SprintTransversalActivityUpdate
    ) -> Optional[SprintTransversalActivity]:
        """Update sprint transversal activity."""
        activity = await self.get_sprint_transversal_activity_by_id(activity_update.id)
        update_data = activity_update.model_dump(exclude_unset=True)

        # Map schema fields to model fields
        field_mapping = {
            'name': 'activity',
            'description': 'meaning',
            'timeSpent': 'time_spent'
        }

        for field, value in update_data.items():
            if field != 'id' and value is not None:
                setattr(activity, field_mapping[field], value)

        try:
            await self.engine.save(activity)
            return activity
        except Exception as e:  # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating sprint transversal activity: {str(e)}"
            )

    async def delete_sprint_transversal_activity(self, activity_id: str) -> bool:
        """Soft delete sprint transversal activity."""
        activity = await self.get_sprint_transversal_activity_by_id(activity_id)

        activity.is_deleted = True
        await self.engine.save(activity)
        return True