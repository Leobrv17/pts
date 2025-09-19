"""Tests unitaires pour ProjectService."""

import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from fastapi import HTTPException

from app.models.project import Project, ProjectStatus, ProjectTransversalActivity
from app.schemas.project import ProjectBase, ProjectUpdate, ProjectTransversalActivityCreate


class TestProjectServiceCreate:
    """Tests pour la création de projets."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, project_service, sample_service_center):
        """Test création réussie d'un projet."""
        # Arrange
        project_data = ProjectBase(
            centerId=str(sample_service_center.id),
            projectName="New Test Project",
            status=ProjectStatus.INPROGRESS,
            technicalLoadRatio=2.0,
            taskStatuses=["TODO", "PROG", "DONE"],
            taskTypes=["TASK", "BUG"]
        )

        # Act
        result = await project_service.create_project(project_data)

        # Assert
        assert result.projectName == project_data.projectName
        assert result.status == project_data.status
        assert result.transversal_vs_technical_workload_ratio == project_data.technicalLoadRatio
        assert result.task_statuses == project_data.taskStatuses
        assert result.task_types == project_data.taskTypes
        assert result.centerId == ObjectId(project_data.centerId)
        project_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_without_center_id(self, project_service):
        """Test création d'un projet sans centre de service."""
        # Arrange
        project_data = ProjectBase(
            centerId=None,
            projectName="Project Without Center",
            status=ProjectStatus.BID,
            technicalLoadRatio=1.0,
            taskStatuses=["TODO"],
            taskTypes=["TASK"]
        )

        # Act
        result = await project_service.create_project(project_data)

        # Assert
        assert result.centerId is None
        assert result.projectName == project_data.projectName
        project_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_database_error(self, project_service):
        """Test gestion d'erreur lors de la création."""
        # Arrange
        project_data = ProjectBase(
            centerId=str(ObjectId()),
            projectName="Failed Project",
            status=ProjectStatus.INPROGRESS,
            technicalLoadRatio=1.0,
            taskStatuses=["TODO"],
            taskTypes=["TASK"]
        )
        project_service.engine.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await project_service.create_project(project_data)

        assert exc_info.value.status_code == 400
        assert "Error creating project" in exc_info.value.detail


class TestProjectServiceRead:
    """Tests pour la lecture de projets."""

    @pytest.mark.asyncio
    async def test_get_project_by_id_success(self, project_service, sample_project):
        """Test récupération réussie d'un projet par ID."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project

        # Act
        result = await project_service.get_project_by_id(str(sample_project.id))

        # Assert
        assert result == sample_project
        project_service.engine.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, project_service, nonexistent_object_id):
        """Test récupération d'un projet inexistant."""
        # Arrange
        project_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await project_service.get_project_by_id(nonexistent_object_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_project_by_id_invalid_id(self, project_service, invalid_object_id):
        """Test récupération avec un ID invalide."""
        # Arrange
        project_service.engine.find_one.return_value = None

        # Act
        result = await project_service.get_project_by_id(invalid_object_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_projects_with_filters(self, project_service, sample_projects_list):
        """Test récupération de projets avec filtres."""
        # Arrange
        filtered_projects = [p for p in sample_projects_list if p.status == ProjectStatus.INPROGRESS]
        project_service.engine.find.return_value = filtered_projects
        project_service.engine.count.return_value = len(filtered_projects)

        # Act
        projects, total = await project_service.get_projects(
            skip=0,
            limit=10,
            center_id=str(sample_projects_list[0].centerId),
            status="In progress"
        )

        # Assert
        assert len(projects) == 1
        assert total == 1
        assert projects[0].status == ProjectStatus.INPROGRESS
        project_service.engine.find.assert_called_once()
        project_service.engine.count.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_projects_no_filters(self, project_service, sample_projects_list):
        """Test récupération de tous les projets."""
        # Arrange
        project_service.engine.find.return_value = sample_projects_list
        project_service.engine.count.return_value = len(sample_projects_list)

        # Act
        projects, total = await project_service.get_projects()

        # Assert
        assert len(projects) == 2
        assert total == 2


class TestProjectServiceUpdate:
    """Tests pour la mise à jour de projets."""

    @pytest.mark.asyncio
    @patch('app.services.project_service.ProjectService._recalculate_project_tasks')
    async def test_update_project_success(self, mock_recalc, project_service, sample_project):
        """Test mise à jour réussie d'un projet."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project
        mock_recalc.return_value = True

        update_data = ProjectUpdate(
            id=str(sample_project.id),
            projectName="Updated Project Name",
            status=ProjectStatus.DONE,
            technicalLoadRatio=3.0
        )

        # Act
        result = await project_service.update_project(update_data)

        # Assert
        assert result.projectName == "Updated Project Name"
        assert result.status == ProjectStatus.DONE
        assert result.transversal_vs_technical_workload_ratio == 3.0
        project_service.engine.save.assert_called_once()
        mock_recalc.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_ratio_unchanged(self, project_service, sample_project):
        """Test mise à jour sans changement de ratio."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project

        update_data = ProjectUpdate(
            id=str(sample_project.id),
            projectName="Updated Name Only"
        )

        # Act
        with patch.object(project_service, '_recalculate_project_tasks') as mock_recalc:
            result = await project_service.update_project(update_data)

            # Assert
            assert result.projectName == "Updated Name Only"
            project_service.engine.save.assert_called_once()
            mock_recalc.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, project_service, nonexistent_object_id):
        """Test mise à jour d'un projet inexistant."""
        # Arrange
        project_service.engine.find_one.return_value = None

        update_data = ProjectUpdate(
            id=nonexistent_object_id,
            projectName="Won't be updated"
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await project_service.update_project(update_data)


class TestProjectServiceDelete:
    """Tests pour la suppression de projets."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, project_service, sample_project):
        """Test suppression réussie d'un projet."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project
        sample_project.is_deleted = False

        # Act
        result = await project_service.delete_project(str(sample_project.id))

        # Assert
        assert result is True
        assert mock_calc_metrics.call_count == len(sample_tasks_list)
        assert project_service.engine.save.call_count == len(sample_tasks_list)

    @pytest.mark.asyncio
    async def test_recalculate_project_tasks_project_not_found(self, project_service, valid_object_id):
        """Test recalcul avec projet inexistant."""
        # Arrange
        project_service.engine.find_one.return_value = None

        # Act
        result = await project_service._recalculate_project_tasks(valid_object_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_recalculate_project_tasks_exception(self, project_service, sample_project):
        """Test gestion d'exception lors du recalcul."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project
        project_service.engine.find.side_effect = Exception("Database error")

        # Act
        result = await project_service._recalculate_project_tasks(sample_project.id)

        # Assert
        assert result is False
        assert sample_project.is_deleted is True
        project_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_service, nonexistent_object_id):
        """Test suppression d'un projet inexistant."""
        # Arrange
        project_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException):
            await project_service.delete_project(nonexistent_object_id)


class TestProjectTransversalActivityService:
    """Tests pour les activités transversales de projet."""

    @pytest.mark.asyncio
    async def test_create_project_transversal_activity_success(self, project_service, sample_project):
        """Test création d'activité transversale."""
        # Arrange
        activity_data = ProjectTransversalActivityCreate(
            projectId=str(sample_project.id),
            activity="New Activity",
            meaning="Activity description"
        )

        # Act
        result = await project_service.create_project_transversal_activity(activity_data)

        # Assert
        assert result.activity == activity_data.activity
        assert result.meaning == activity_data.meaning
        assert result.project_id == ObjectId(activity_data.projectId)
        project_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_default_transversal_activities(self, project_service, sample_project):
        """Test création des activités par défaut."""
        # Arrange
        with patch.object(project_service, 'create_project_transversal_activity') as mock_create:
            mock_create.return_value = AsyncMock()

            # Act
            await project_service.create_default_transversal_activities(str(sample_project.id))

            # Assert
            assert mock_create.call_count == len(project_service._default_activities)

    @pytest.mark.asyncio
    async def test_get_project_transversal_activities_by_project(self, project_service,
                                                                 sample_project_transversal_activity):
        """Test récupération des activités transversales par projet."""
        # Arrange
        activities = [sample_project_transversal_activity]
        project_service.engine.find.return_value = activities

        # Act
        result = await project_service.get_project_transversal_activities_by_project(
            str(sample_project_transversal_activity.project_id)
        )

        # Assert
        assert len(result) == 1
        assert result[0] == sample_project_transversal_activity
        project_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_transversal_activity_success(self, project_service,
                                                               sample_project_transversal_activity):
        """Test mise à jour d'activité transversale."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project_transversal_activity

        updated_activity = ProjectTransversalActivity(
            id=sample_project_transversal_activity.id,
            project_id=sample_project_transversal_activity.project_id,
            activity="Updated Activity",
            meaning="Updated description"
        )

        # Act
        result = await project_service.update_project_transversal_activity(updated_activity)

        # Assert
        assert result.activity == "Updated Activity"
        assert result.meaning == "Updated description"
        project_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_transversal_activity_success(self, project_service,
                                                               sample_project_transversal_activity):
        """Test suppression d'activité transversale."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project_transversal_activity
        sample_project_transversal_activity.is_deleted = False

        # Act
        result = await project_service.delete_project_transversal_activity(str(sample_project_transversal_activity.id))

        # Assert
        assert result is True
        assert sample_project_transversal_activity.is_deleted is True
        project_service.engine.save.assert_called_once()


class TestProjectServiceRecalculation:
    """Tests pour le recalcul des tâches."""

    @pytest.mark.asyncio
    @patch('app.services.project_service.calculate_task_metrics')
    async def test_recalculate_project_tasks_success(self, mock_calc_metrics, project_service, sample_project,
                                                     sample_tasks_list):
        """Test recalcul des tâches du projet."""
        # Arrange
        project_service.engine.find_one.return_value = sample_project
        project_service.engine.find.return_value = sample_tasks_list
        mock_calc_metrics.return_value = {
            "technical_load": 3.0,
            "delta": 0.5,
            "progress": 60.0
        }

        # Act
        result = await project_service._recalculate_project_tasks(sample_project.id)

        # Assert
        assert result is True