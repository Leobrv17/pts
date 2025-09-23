"""Tests unitaires pour CascadeDeletionService."""

import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from fastapi import HTTPException

from app.models.project import Project
from app.models.service_center import ServiceCenter
from app.models.sprint import Sprint, SprintTransversalActivity
from app.models.task import Task
from app.services.cascade_deletion_service import CascadeDeletionService


class TestCascadeDeletionServiceBase:
    """Tests de base pour CascadeDeletionService."""

    def test_cascade_deletion_service_init(self, mock_engine):
        """Test d'initialisation du service."""
        service = CascadeDeletionService(mock_engine)
        assert service.engine == mock_engine


class TestCascadeDeletionServiceDelete:
    """Tests pour les suppressions individuelles."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, cascade_deletion_service, sample_task):
        """Test suppression réussie d'une tâche."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_task
        sample_task.is_deleted = False

        # Act
        result = await cascade_deletion_service.delete_task(str(sample_task.id))

        # Assert
        assert result is True
        assert sample_task.is_deleted is True
        cascade_deletion_service.engine.save.assert_called_once_with(sample_task)

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, cascade_deletion_service, nonexistent_object_id):
        """Test suppression d'une tâche inexistante."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = None

        # Act
        result = await cascade_deletion_service.delete_task(nonexistent_object_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_task_cascade_flag(self, cascade_deletion_service, sample_task):
        """Test suppression avec flag cascade."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_task

        # Act
        result = await cascade_deletion_service.delete_task(str(sample_task.id), is_cascade=True)

        # Assert
        assert result is True
        assert sample_task.is_cascade_deleted is True
        cascade_deletion_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_sprint_transversal_activity_success(self, cascade_deletion_service,
                                                             sample_sprint_transversal_activity):
        """Test suppression d'activité transversale de sprint."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_sprint_transversal_activity

        # Act
        result = await cascade_deletion_service.delete_sprint_transversal_activity(
            str(sample_sprint_transversal_activity.id)
        )

        # Assert
        assert result is True
        assert sample_sprint_transversal_activity.is_deleted is True
        cascade_deletion_service.engine.save.assert_called_once()


class TestCascadeDeletionServiceSprintCascade:
    """Tests pour la suppression en cascade de sprints."""

    @pytest.mark.asyncio
    async def test_delete_sprint_with_cascade_success(self, cascade_deletion_service, sample_sprint):
        """Test suppression en cascade d'un sprint."""
        # Arrange
        sample_tasks = [Task(
            id=ObjectId(),
            sprintId=sample_sprint.id,
            projectId=sample_sprint.projectId,
            key=f"TASK-{i}",
            summary=f"Task {i}"
        ) for i in range(3)]

        sample_activities = [SprintTransversalActivity(
            id=ObjectId(),
            sprintId=sample_sprint.id,
            activity=f"Activity {i}",
            meaning=f"Meaning {i}"
        ) for i in range(2)]

        cascade_deletion_service.engine.find_one.return_value = sample_sprint
        cascade_deletion_service.engine.find.side_effect = [sample_tasks, sample_activities]

        with patch.object(cascade_deletion_service, 'delete_task', return_value=True) as mock_delete_task, \
             patch.object(cascade_deletion_service, 'delete_sprint_transversal_activity',
                         return_value=True) as mock_delete_activity:

            # Act
            result = await cascade_deletion_service.delete_sprint_with_cascade(str(sample_sprint.id))

            # Assert
            assert result is True
            assert sample_sprint.is_deleted is True
            assert mock_delete_task.call_count == 3
            assert mock_delete_activity.call_count == 2
            cascade_deletion_service.engine.save.assert_called()

    @pytest.mark.asyncio
    async def test_delete_sprint_with_cascade_not_found(self, cascade_deletion_service, nonexistent_object_id):
        """Test suppression en cascade d'un sprint inexistant."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = None

        # Act
        result = await cascade_deletion_service.delete_sprint_with_cascade(nonexistent_object_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_sprint_with_cascade_individual_only(self, cascade_deletion_service, sample_sprint):
        """Test suppression individuelle uniquement."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_sprint
        cascade_deletion_service.engine.find.return_value = []

        # Act
        result = await cascade_deletion_service.delete_sprint_with_cascade(
            str(sample_sprint.id),
            is_cascade=False
        )

        # Assert
        assert result is True
        assert sample_sprint.is_deleted is True
        cascade_deletion_service.engine.save.assert_called_once_with(sample_sprint)


class TestCascadeDeletionServiceProjectCascade:
    """Tests pour la suppression en cascade de projets."""

    @pytest.mark.asyncio
    async def test_delete_project_with_cascade_success(self, cascade_deletion_service, sample_project):
        """Test suppression en cascade d'un projet."""
        # Arrange
        sample_sprints = [Sprint(
            id=ObjectId(),
            projectId=sample_project.id,
            sprintName=f"Sprint {i}",
            startDate=sample_datetime,
            dueDate=sample_future_datetime,
            capacity=40.0
        ) for i in range(2)]

        cascade_deletion_service.engine.find_one.return_value = sample_project
        cascade_deletion_service.engine.find.return_value = sample_sprints

        with patch.object(cascade_deletion_service, 'delete_sprint_with_cascade',
                         return_value=True) as mock_delete_sprint:

            # Act
            result = await cascade_deletion_service.delete_project_with_cascade(str(sample_project.id))

            # Assert
            assert result is True
            assert sample_project.is_deleted is True
            assert mock_delete_sprint.call_count == 2
            cascade_deletion_service.engine.save.assert_called()

    @pytest.mark.asyncio
    async def test_delete_project_with_cascade_not_found(self, cascade_deletion_service, nonexistent_object_id):
        """Test suppression en cascade d'un projet inexistant."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = None

        # Act
        result = await cascade_deletion_service.delete_project_with_cascade(nonexistent_object_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_project_with_cascade_individual_only(self, cascade_deletion_service, sample_project):
        """Test suppression individuelle d'un projet uniquement."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_project
        cascade_deletion_service.engine.find.return_value = []

        # Act
        result = await cascade_deletion_service.delete_project_with_cascade(
            str(sample_project.id),
            is_cascade=False
        )

        # Assert
        assert result is True
        assert sample_project.is_deleted is True
        cascade_deletion_service.engine.save.assert_called_once_with(sample_project)


class TestCascadeDeletionServiceCenterCascade:
    """Tests pour la suppression en cascade de centres de service."""

    @pytest.mark.asyncio
    async def test_delete_service_center_with_cascade_success(self, cascade_deletion_service, sample_service_center):
        """Test suppression en cascade d'un centre de service."""
        # Arrange
        sample_projects = [Project(
            id=ObjectId(),
            centerId=sample_service_center.id,
            projectName=f"Project {i}",
            status="In progress"
        ) for i in range(2)]

        cascade_deletion_service.engine.find_one.return_value = sample_service_center
        cascade_deletion_service.engine.find.return_value = sample_projects

        with patch.object(cascade_deletion_service, 'delete_project_with_cascade',
                         return_value=True) as mock_delete_project:

            # Act
            result = await cascade_deletion_service.delete_service_center_with_cascade(
                str(sample_service_center.id)
            )

            # Assert
            assert result is True
            assert sample_service_center.is_deleted is True
            assert mock_delete_project.call_count == 2
            cascade_deletion_service.engine.save.assert_called()

    @pytest.mark.asyncio
    async def test_delete_service_center_with_cascade_not_found(self, cascade_deletion_service,
                                                               nonexistent_object_id):
        """Test suppression en cascade d'un centre inexistant."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = None

        # Act
        result = await cascade_deletion_service.delete_service_center_with_cascade(nonexistent_object_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_service_center_with_cascade_no_projects(self, cascade_deletion_service,
                                                                 sample_service_center):
        """Test suppression d'un centre sans projets."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_service_center
        cascade_deletion_service.engine.find.return_value = []

        # Act
        result = await cascade_deletion_service.delete_service_center_with_cascade(
            str(sample_service_center.id)
        )

        # Assert
        assert result is True
        assert sample_service_center.is_deleted is True
        cascade_deletion_service.engine.save.assert_called_once_with(sample_service_center)


class TestCascadeDeletionServiceErrorHandling:
    """Tests pour la gestion d'erreurs."""

    @pytest.mark.asyncio
    async def test_delete_task_database_error(self, cascade_deletion_service, sample_task):
        """Test gestion d'erreur base de données lors de suppression de tâche."""
        # Arrange
        cascade_deletion_service.engine.find_one.return_value = sample_task
        cascade_deletion_service.engine.save.side_effect = Exception("Database error")

        # Act
        result = await cascade_deletion_service.delete_task(str(sample_task.id))

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_sprint_cascade_partial_failure(self, cascade_deletion_service, sample_sprint):
        """Test échec partiel lors de suppression en cascade de sprint."""
        # Arrange
        sample_tasks = [Task(
            id=ObjectId(),
            sprintId=sample_sprint.id,
            projectId=sample_sprint.projectId,
            key="TASK-1",
            summary="Task 1"
        )]

        cascade_deletion_service.engine.find_one.return_value = sample_sprint
        cascade_deletion_service.engine.find.side_effect = [sample_tasks, []]

        with patch.object(cascade_deletion_service, 'delete_task', return_value=False) as mock_delete_task:

            # Act
            result = await cascade_deletion_service.delete_sprint_with_cascade(str(sample_sprint.id))

            # Assert
            assert result is True  # Le sprint principal est supprimé même si les tâches échouent
            assert mock_delete_task.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_invalid_object_id(self, cascade_deletion_service, invalid_object_id):
        """Test suppression avec ID invalide."""
        # Act
        result = await cascade_deletion_service.delete_task(invalid_object_id)

        # Assert
        assert result is False


class TestCascadeDeletionServiceUtilities:
    """Tests pour les méthodes utilitaires."""

    @pytest.mark.asyncio
    async def test_get_cascade_deleted_elements_project(self, cascade_deletion_service, sample_project):
        """Test récupération des éléments supprimés en cascade pour un projet."""
        # Arrange
        deleted_sprints = [Sprint(
            id=ObjectId(),
            projectId=sample_project.id,
            sprintName="Deleted Sprint",
            is_cascade_deleted=True,
            startDate=sample_datetime,
            dueDate=sample_future_datetime,
            capacity=40.0
        )]

        cascade_deletion_service.engine.find.return_value = deleted_sprints

        # Act
        result = await cascade_deletion_service.get_cascade_deleted_elements("project", str(sample_project.id))

        # Assert
        assert "sprints" in result
        assert len(result["sprints"]) == 1
        assert result["sprints"][0] == str(deleted_sprints[0].id)

    @pytest.mark.asyncio
    async def test_get_cascade_deleted_elements_invalid_type(self, cascade_deletion_service, valid_object_id):
        """Test récupération avec type d'élément invalide."""
        # Act
        result = await cascade_deletion_service.get_cascade_deleted_elements("invalid_type", str(valid_object_id))

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_cascade_deleted_elements_empty_result(self, cascade_deletion_service, sample_project):
        """Test récupération sans éléments supprimés."""
        # Arrange
        cascade_deletion_service.engine.find.return_value = []

        # Act
        result = await cascade_deletion_service.get_cascade_deleted_elements("project", str(sample_project.id))

        # Assert
        assert "sprints" in result
        assert len(result["sprints"]) == 0