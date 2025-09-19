"""Tests unitaires pour SprintService."""

import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta

from app.models.sprint import Sprint, SprintStatus, SprintTransversalActivity
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintTransversalActivityUpdate


class TestSprintServiceCreate:
    """Tests pour la création de sprints."""

    @pytest.mark.asyncio
    async def test_create_sprint_success(self, sprint_service, sample_project):
        """Test création réussie d'un sprint."""
        # Arrange
        now = datetime.now(timezone.utc)
        sprint_data = SprintCreate(
            projectId=str(sample_project.id),
            sprintName="New Sprint",
            status=SprintStatus.TODO,
            startDate=now,
            dueDate=now + timedelta(days=14),
            capacity=30.0
        )

        # Act
        result = await sprint_service.create_sprint(sprint_data)

        # Assert
        assert result.sprintName == sprint_data.sprintName
        assert result.status == sprint_data.status
        assert result.capacity == sprint_data.capacity
        assert result.projectId == ObjectId(sprint_data.projectId)
        assert result.startDate == sprint_data.startDate
        assert result.dueDate == sprint_data.dueDate
        assert result.sprint_transversal_activities == []
        assert result.task == []
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sprint_database_error(self, sprint_service, sample_project):
        """Test gestion d'erreur lors de la création."""
        # Arrange
        now = datetime.now(timezone.utc)
        sprint_data = SprintCreate(
            projectId=str(sample_project.id),
            sprintName="Failed Sprint",
            startDate=now,
            dueDate=now + timedelta(days=7),
            capacity=20.0
        )
        sprint_service.engine.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await sprint_service.create_sprint(sprint_data)

        assert exc_info.value.status_code == 400
        assert "Error creating sprint" in exc_info.value.detail


class TestSprintServiceRead:
    """Tests pour la lecture de sprints."""

    @pytest.mark.asyncio
    async def test_get_sprint_by_id_success(self, sprint_service, sample_sprint):
        """Test récupération réussie d'un sprint par ID."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint

        # Act
        result = await sprint_service.get_sprint_by_id(str(sample_sprint.id))

        # Assert
        assert result == sample_sprint
        sprint_service.engine.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sprint_by_id_not_found(self, sprint_service, nonexistent_object_id):
        """Test récupération d'un sprint inexistant."""
        # Arrange
        sprint_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await sprint_service.get_sprint_by_id(nonexistent_object_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_sprint_by_id_invalid_id(self, sprint_service, invalid_object_id):
        """Test récupération avec un ID invalide."""
        # Act
        result = await sprint_service.get_sprint_by_id(invalid_object_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_sprints_with_filters(self, sprint_service, sample_project):
        """Test récupération de sprints avec filtres."""
        # Arrange
        sprint1 = Sprint(
            id=ObjectId(),
            projectId=sample_project.id,
            sprintName="Sprint 1",
            status=SprintStatus.TODO,
            startDate=datetime.now(timezone.utc),
            dueDate=datetime.now(timezone.utc) + timedelta(days=14),
            capacity=40.0
        )
        sprint2 = Sprint(
            id=ObjectId(),
            projectId=sample_project.id,
            sprintName="Sprint 2",
            status=SprintStatus.INPROGRESS,
            startDate=datetime.now(timezone.utc),
            dueDate=datetime.now(timezone.utc) + timedelta(days=14),
            capacity=35.0
        )

        # Simuler le filtrage côté base de données
        filtered_sprints = [sprint1]  # Seul le sprint TODO
        sprint_service.engine.find.return_value = filtered_sprints

        # Act
        sprints, total = await sprint_service.get_sprints(
            project_id=str(sample_project.id),
            status="To do"
        )

        # Assert
        assert len(sprints) == 1
        assert total == 1
        assert sprints[0].status == SprintStatus.TODO
        sprint_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sprints_by_ids(self, sprint_service, sample_project):
        """Test récupération de sprints par liste d'IDs."""
        # Arrange
        sprint_ids = [str(ObjectId()), str(ObjectId())]
        mock_sprints = [
            Sprint(
                id=ObjectId(sprint_ids[0]),
                projectId=sample_project.id,
                sprintName="Sprint 1",
                status=SprintStatus.TODO,
                startDate=datetime.now(timezone.utc),
                dueDate=datetime.now(timezone.utc) + timedelta(days=14),
                capacity=40.0
            )
        ]
        sprint_service.engine.find.return_value = mock_sprints

        # Act
        sprints, total = await sprint_service.get_sprints(sprint_ids=sprint_ids)

        # Assert
        assert len(sprints) == 1
        assert total == 1
        sprint_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_relevant_sprints_by_project(self, sprint_service, sample_project):
        """Test récupération des sprints pertinents pour un projet."""
        # Arrange
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        relevant_sprints = [
            Sprint(
                id=ObjectId(),
                projectId=sample_project.id,
                sprintName="Current Sprint",
                status=SprintStatus.INPROGRESS,
                startDate=datetime.now(timezone.utc),
                dueDate=future_date,
                capacity=40.0
            ),
            Sprint(
                id=ObjectId(),
                projectId=sample_project.id,
                sprintName="Future Sprint",
                status=SprintStatus.TODO,
                startDate=future_date,
                dueDate=future_date + timedelta(days=14),
                capacity=35.0
            )
        ]
        sprint_service.engine.find.return_value = relevant_sprints

        # Act
        result = await sprint_service.get_relevant_sprints_by_project(str(sample_project.id))

        # Assert
        assert len(result) == 2
        assert all(isinstance(sprint, dict) for sprint in result)
        assert all("id" in sprint and "name" in sprint for sprint in result)
        assert result[0]["name"] == "Current Sprint"
        assert result[1]["name"] == "Future Sprint"

    @pytest.mark.asyncio
    async def test_get_relevant_sprints_invalid_project_id(self, sprint_service, invalid_object_id):
        """Test récupération avec ID projet invalide."""
        # Act
        result = await sprint_service.get_relevant_sprints_by_project(invalid_object_id)

        # Assert
        assert result == []


class TestSprintServiceUpdate:
    """Tests pour la mise à jour de sprints."""

    @pytest.mark.asyncio
    async def test_update_sprint_success(self, sprint_service, sample_sprint, sample_project):
        """Test mise à jour réussie d'un sprint."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint
        new_due_date = sample_sprint.dueDate + timedelta(days=7)

        update_data = SprintUpdate(
            id=str(sample_sprint.id),
            sprintName="Updated Sprint",
            status=SprintStatus.INPROGRESS,
            dueDate=new_due_date,
            capacity=50.0
        )

        # Act
        result = await sprint_service.update_sprint(update_data)

        # Assert
        assert result.sprintName == "Updated Sprint"
        assert result.status == SprintStatus.INPROGRESS
        assert result.dueDate == new_due_date
        assert result.capacity == 50.0
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_sprint_with_project_change(self, sprint_service, sample_sprint, sample_project):
        """Test mise à jour avec changement de projet."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint
        new_project_id = ObjectId()

        update_data = SprintUpdate(
            id=str(sample_sprint.id),
            projectId=str(new_project_id)
        )

        # Act
        result = await sprint_service.update_sprint(update_data)

        # Assert
        assert result.projectId == new_project_id
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_sprint_not_found(self, sprint_service, nonexistent_object_id):
        """Test mise à jour d'un sprint inexistant."""
        # Arrange
        sprint_service.engine.find_one.return_value = None

        update_data = SprintUpdate(
            id=nonexistent_object_id,
            sprintName="Won't be updated"
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await sprint_service.update_sprint(update_data)

    @pytest.mark.asyncio
    async def test_update_sprint_database_error(self, sprint_service, sample_sprint):
        """Test gestion d'erreur lors de la mise à jour."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint
        sprint_service.engine.save.side_effect = Exception("Database error")

        update_data = SprintUpdate(
            id=str(sample_sprint.id),
            sprintName="Error Sprint"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await sprint_service.update_sprint(update_data)

        assert exc_info.value.status_code == 400
        assert "Error updating sprint" in exc_info.value.detail


class TestSprintServiceDelete:
    """Tests pour la suppression de sprints."""

    @pytest.mark.asyncio
    async def test_delete_sprint_success(self, sprint_service, sample_sprint):
        """Test suppression réussie d'un sprint."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint
        sample_sprint.is_deleted = False

        # Act
        result = await sprint_service.delete_sprint(str(sample_sprint.id))

        # Assert
        assert result is True
        assert sample_sprint.is_deleted is True
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_sprint_not_found(self, sprint_service, nonexistent_object_id):
        """Test suppression d'un sprint inexistant."""
        # Arrange
        sprint_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException):
            await sprint_service.delete_sprint(nonexistent_object_id)


class TestSprintTransversalActivityService:
    """Tests pour les activités transversales de sprint."""

    @pytest.mark.asyncio
    async def test_create_sprint_transversal_activity_success(self, sprint_service, sample_sprint):
        """Test création d'activité transversale."""
        # Arrange
        activity = SprintTransversalActivity(
            sprintId=sample_sprint.id,
            activity="New Sprint Activity",
            meaning="Activity description",
            time_spent=5.0
        )

        # Act
        result = await sprint_service.create_sprint_transversal_activity(activity)

        # Assert
        assert result == activity
        sprint_service.engine.save.assert_called_once_with(activity)

    @pytest.mark.asyncio
    async def test_create_sprint_transversal_activity_error(self, sprint_service, sample_sprint):
        """Test gestion d'erreur lors de la création d'activité."""
        # Arrange
        activity = SprintTransversalActivity(
            sprintId=sample_sprint.id,
            activity="Error Activity",
            meaning="Will fail",
            time_spent=0.0
        )
        sprint_service.engine.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await sprint_service.create_sprint_transversal_activity(activity)

        assert exc_info.value.status_code == 400
        assert "Error creating sprint transversal activity" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_sprint_transversal_activity_by_id_success(self, sprint_service,
                                                                 sample_sprint_transversal_activity):
        """Test récupération d'activité transversale par ID."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint_transversal_activity

        # Act
        result = await sprint_service.get_sprint_transversal_activity_by_id(str(sample_sprint_transversal_activity.id))

        # Assert
        assert result == sample_sprint_transversal_activity
        sprint_service.engine.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sprint_transversal_activity_by_id_not_found(self, sprint_service, nonexistent_object_id):
        """Test récupération d'activité inexistante."""
        # Arrange
        sprint_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await sprint_service.get_sprint_transversal_activity_by_id(nonexistent_object_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_sprint_transversal_activities_by_sprint(self, sprint_service, sample_sprint,
                                                               sample_sprint_transversal_activity):
        """Test récupération des activités par sprint."""
        # Arrange
        activities = [sample_sprint_transversal_activity]
        sprint_service.engine.find.return_value = activities

        # Act
        result = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sample_sprint.id))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_sprint_transversal_activity
        sprint_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sprint_transversal_activities_by_sprint_empty(self, sprint_service, sample_sprint):
        """Test récupération d'activités d'un sprint vide."""
        # Arrange
        sprint_service.engine.find.return_value = []

        # Act
        result = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sample_sprint.id))

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_sprint_transversal_activities_exception(self, sprint_service, sample_sprint):
        """Test gestion d'exception lors de la récupération."""
        # Arrange
        sprint_service.engine.find.side_effect = Exception("Database error")

        # Act
        result = await sprint_service.get_sprint_transversal_activities_by_sprint(str(sample_sprint.id))

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_update_sprint_transversal_activity_success(self, sprint_service, sample_sprint_transversal_activity):
        """Test mise à jour d'activité transversale."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint_transversal_activity

        update_data = SprintTransversalActivityUpdate(
            id=str(sample_sprint_transversal_activity.id),
            name="Updated Activity",
            description="Updated description",
            timeSpent=10.0
        )

        # Act
        result = await sprint_service.update_sprint_transversal_activity(update_data)

        # Assert
        assert result.activity == "Updated Activity"
        assert result.meaning == "Updated description"
        assert result.time_spent == 10.0
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_sprint_transversal_activity_not_found(self, sprint_service, nonexistent_object_id):
        """Test mise à jour d'activité inexistante."""
        # Arrange
        sprint_service.engine.find_one.return_value = None

        update_data = SprintTransversalActivityUpdate(
            id=nonexistent_object_id,
            name="Won't be updated"
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await sprint_service.update_sprint_transversal_activity(update_data)

    @pytest.mark.asyncio
    async def test_update_sprint_transversal_activity_partial(self, sprint_service, sample_sprint_transversal_activity):
        """Test mise à jour partielle d'activité transversale."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint_transversal_activity
        original_meaning = sample_sprint_transversal_activity.meaning
        original_time = sample_sprint_transversal_activity.time_spent

        update_data = SprintTransversalActivityUpdate(
            id=str(sample_sprint_transversal_activity.id),
            name="Only Name Updated"
        )

        # Act
        result = await sprint_service.update_sprint_transversal_activity(update_data)

        # Assert
        assert result.activity == "Only Name Updated"
        assert result.meaning == original_meaning  # Pas changé
        assert result.time_spent == original_time  # Pas changé
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_sprint_transversal_activity_success(self, sprint_service, sample_sprint_transversal_activity):
        """Test suppression d'activité transversale."""
        # Arrange
        sprint_service.engine.find_one.return_value = sample_sprint_transversal_activity
        sample_sprint_transversal_activity.is_deleted = False

        # Act
        result = await sprint_service.delete_sprint_transversal_activity(str(sample_sprint_transversal_activity.id))

        # Assert
        assert result is True
        assert sample_sprint_transversal_activity.is_deleted is True
        sprint_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_sprint_transversal_activity_not_found(self, sprint_service, nonexistent_object_id):
        """Test suppression d'activité inexistante."""
        # Arrange
        sprint_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException):
            await sprint_service.delete_sprint_transversal_activity(nonexistent_object_id)