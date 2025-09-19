"""Tests unitaires pour TaskService."""

import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from fastapi import HTTPException

from app.models.task import Task, TaskStatus, TaskType, TASKRFT, TaskDeliveryStatus
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate


class TestTaskServiceValidation:
    """Tests pour les validations d'enum."""

    def test_validate_and_convert_status_success(self, task_service):
        """Test validation réussie du statut."""
        # Act & Assert
        assert task_service._validate_and_convert_status("TODO") == TaskStatus.TODO
        assert task_service._validate_and_convert_status("PROG") == TaskStatus.INPROGRESS
        assert task_service._validate_and_convert_status("DONE") == TaskStatus.DONE

    def test_validate_and_convert_status_invalid(self, task_service):
        """Test validation échouée du statut."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            task_service._validate_and_convert_status("INVALID_STATUS")

        assert exc_info.value.status_code == 400
        assert "Invalid task status" in exc_info.value.detail

    def test_validate_and_convert_type_success(self, task_service):
        """Test validation réussie du type."""
        # Act & Assert
        assert task_service._validate_and_convert_type("TASK") == TaskType.TASK
        assert task_service._validate_and_convert_type("BUG") == TaskType.BUG

    def test_validate_and_convert_type_invalid(self, task_service):
        """Test validation échouée du type."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            task_service._validate_and_convert_type("INVALID_TYPE")

        assert exc_info.value.status_code == 400
        assert "Invalid task type" in exc_info.value.detail

    def test_validate_and_convert_rft_success(self, task_service):
        """Test validation réussie du RFT."""
        # Act & Assert
        assert task_service._validate_and_convert_rft("") == TASKRFT.DEFAULT
        assert task_service._validate_and_convert_rft("OK") == TASKRFT.OK
        assert task_service._validate_and_convert_rft("KO") == TASKRFT.KO

    def test_validate_and_convert_delivery_status_success(self, task_service):
        """Test validation réussie du delivery status."""
        # Act & Assert
        assert task_service._validate_and_convert_delivery_status("") == TaskDeliveryStatus.DEFAULT
        assert task_service._validate_and_convert_delivery_status("OK") == TaskDeliveryStatus.OK
        assert task_service._validate_and_convert_delivery_status("KO") == TaskDeliveryStatus.KO


class TestTaskServiceCalculation:
    """Tests pour le calcul des métriques de tâches."""

    @pytest.mark.asyncio
    @patch('app.services.task_service.calculate_task_metrics')
    async def test_calculate_and_update_fields_success(self, mock_calc_metrics, task_service, sample_task,
                                                       sample_project):
        """Test calcul et mise à jour des champs."""
        # Arrange
        task_service.engine.find_one.return_value = sample_project
        mock_calc_metrics.return_value = {
            "technical_load": 2.5,
            "delta": 0.0,
            "progress": 40.0
        }
        sample_task.deliveryStatus = TaskDeliveryStatus.DEFAULT
        sample_task.status = TaskStatus.TODO

        # Act
        result = await task_service._calculate_and_update_fields(sample_task, initialize_time_remaining=True)

        # Assert
        assert result.technicalLoad == 2.5
        assert result.delta == 0.0
        assert result.progress == 40.0
        assert result.timeRemaining == 2.5
        mock_calc_metrics.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.task_service.calculate_task_metrics')
    async def test_calculate_and_update_fields_done_task_auto_delivery(self, mock_calc_metrics, task_service,
                                                                       sample_task, sample_project):
        """Test mise à jour automatique du delivery status pour une tâche terminée."""
        # Arrange
        task_service.engine.find_one.return_value = sample_project
        mock_calc_metrics.return_value = {
            "technical_load": 2.5,
            "delta": 0.0,
            "progress": 100.0
        }
        sample_task.status = TaskStatus.DONE
        sample_task.deliveryStatus = TaskDeliveryStatus.DEFAULT

        # Act
        result = await task_service._calculate_and_update_fields(sample_task)

        # Assert
        assert result.deliveryStatus == TaskDeliveryStatus.OK

    @pytest.mark.asyncio
    async def test_calculate_and_update_fields_no_project(self, task_service, sample_task):
        """Test calcul sans projet trouvé."""
        # Arrange
        task_service.engine.find_one.return_value = None

        # Act
        result = await task_service._calculate_and_update_fields(sample_task)

        # Assert
        assert result == sample_task  # Pas de modification


class TestTaskServiceCreate:
    """Tests pour la création de tâches."""

    @pytest.mark.asyncio
    @patch('app.services.task_service.TaskService._calculate_and_update_fields')
    async def test_create_task_success(self, mock_calc_update, task_service, sample_sprint, sample_project,
                                       valid_object_id):
        """Test création réussie d'une tâche."""
        # Arrange
        task_data = TaskCreate(
            sprintId=str(sample_sprint.id),
            projectId=str(sample_project.id),
            key="NEW-001",
            summary="New Task Summary",
            storyPoints=3.0,
            status="TODO",
            type="TASK",
            assignee=[str(valid_object_id)]
        )

        mock_calc_update.return_value = AsyncMock(spec=Task)

        # Act
        result = await task_service.create_task(task_data)

        # Assert
        assert result is not None
        mock_calc_update.assert_called_once()
        task_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_invalid_status(self, task_service, sample_sprint, sample_project):
        """Test création avec statut invalide."""
        # Arrange
        task_data = TaskCreate(
            sprintId=str(sample_sprint.id),
            projectId=str(sample_project.id),
            key="FAIL-001",
            summary="Failed Task",
            status="INVALID_STATUS",
            type="TASK"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await task_service.create_task(task_data)

        assert exc_info.value.status_code == 400
        assert "Invalid task status" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_task_database_error(self, task_service, sample_sprint, sample_project):
        """Test gestion d'erreur lors de la création."""
        # Arrange
        task_data = TaskCreate(
            sprintId=str(sample_sprint.id),
            projectId=str(sample_project.id),
            key="ERROR-001",
            summary="Error Task",
            status="TODO",
            type="TASK"
        )

        with patch.object(task_service, '_calculate_and_update_fields') as mock_calc:
            mock_calc.return_value = AsyncMock(spec=Task)
            task_service.engine.save.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await task_service.create_task(task_data)

            assert exc_info.value.status_code == 400
            assert "Error creating task" in exc_info.value.detail


class TestTaskServiceRead:
    """Tests pour la lecture de tâches."""

    @pytest.mark.asyncio
    async def test_get_task_by_id_success(self, task_service, sample_task):
        """Test récupération réussie d'une tâche par ID."""
        # Arrange
        task_service.engine.find_one.return_value = sample_task

        # Act
        result = await task_service.get_task_by_id(str(sample_task.id))

        # Assert
        assert result == sample_task
        task_service.engine.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, task_service, nonexistent_object_id):
        """Test récupération d'une tâche inexistante."""
        # Arrange
        task_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await task_service.get_task_by_id(nonexistent_object_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_task_by_id_invalid_id(self, task_service, invalid_object_id):
        """Test récupération avec un ID invalide."""
        # Act
        result = await task_service.get_task_by_id(invalid_object_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_tasks_by_sprint_success(self, task_service, sample_tasks_list, sample_sprint):
        """Test récupération des tâches par sprint."""
        # Arrange
        task_service.engine.find.return_value = sample_tasks_list

        # Act
        result = await task_service.get_tasks_by_sprint(str(sample_sprint.id))

        # Assert
        assert len(result) == 2
        assert result == sample_tasks_list
        task_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tasks_by_sprint_empty(self, task_service, sample_sprint):
        """Test récupération des tâches d'un sprint vide."""
        # Arrange
        task_service.engine.find.return_value = []

        # Act
        result = await task_service.get_tasks_by_sprint(str(sample_sprint.id))

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_tasks_by_sprint_exception(self, task_service, sample_sprint):
        """Test gestion d'exception lors de la récupération."""
        # Arrange
        task_service.engine.find.side_effect = Exception("Database error")

        # Act
        result = await task_service.get_tasks_by_sprint(str(sample_sprint.id))

        # Assert
        assert result == []


class TestTaskServiceUpdate:
    """Tests pour la mise à jour de tâches."""

    @pytest.mark.asyncio
    @patch('app.services.task_service.TaskService._calculate_and_update_fields')
    async def test_update_task_success(self, mock_calc_update, task_service, sample_task):
        """Test mise à jour réussie d'une tâche."""
        # Arrange
        task_service.engine.find_one.return_value = sample_task
        mock_calc_update.return_value = sample_task

        update_data = TaskUpdate(
            id=str(sample_task.id),
            summary="Updated Summary",
            storyPoints=8.0,
            status="PROG"
        )

        # Act
        result = await task_service.update_task(update_data)

        # Assert
        assert result.summary == "Updated Summary"
        assert result.storyPoints == 8.0
        assert result.status == TaskStatus.INPROGRESS
        mock_calc_update.assert_called_once()
        task_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, task_service, nonexistent_object_id):
        """Test mise à jour d'une tâche inexistante."""
        # Arrange
        task_service.engine.find_one.return_value = None

        update_data = TaskUpdate(
            id=nonexistent_object_id,
            summary="Won't be updated"
        )

        # Act
        result = await task_service.update_task(update_data)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch('app.services.task_service.TaskService._calculate_and_update_fields')
    async def test_update_task_with_assignees(self, mock_calc_update, task_service, sample_task, valid_object_id,
                                              another_object_id):
        """Test mise à jour avec assignation d'utilisateurs."""
        # Arrange
        task_service.engine.find_one.return_value = sample_task
        mock_calc_update.return_value = sample_task

        update_data = TaskUpdate(
            id=str(sample_task.id),
            assignee=[str(valid_object_id), str(another_object_id)]
        )

        # Act
        result = await task_service.update_task(update_data)

        # Assert
        assert len(result.assignee) == 2
        assert valid_object_id in result.assignee
        assert another_object_id in result.assignee
        mock_calc_update.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.task_service.TaskService._calculate_and_update_fields')
    async def test_update_task_time_remaining_logic(self, mock_calc_update, task_service, sample_task, sample_project):
        """Test logique de réinitialisation du temps restant."""
        # Arrange
        task_service.engine.find_one.side_effect = [sample_task, sample_project]
        sample_task.storyPoints = 5.0
        sample_task.timeRemaining = 2.5  # Égal au technical load initial
        mock_calc_update.return_value = sample_task

        update_data = TaskUpdate(
            id=str(sample_task.id),
            storyPoints=10.0  # Changement des story points
        )

        # Act
        await task_service.update_task(update_data)

        # Assert
        # Vérifier que _calculate_and_update_fields a été appelé avec should_reinitialize_time_remaining=True
        mock_calc_update.assert_called_once()
        call_args = mock_calc_update.call_args
        assert call_args[1]['initialize_time_remaining'] == True


class TestTaskServiceDelete:
    """Tests pour la suppression de tâches."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, task_service, sample_task):
        """Test suppression réussie d'une tâche."""
        # Arrange
        task_service.engine.find_one.return_value = sample_task
        sample_task.is_deleted = False

        # Act
        result = await task_service.delete_task(str(sample_task.id))

        # Assert
        assert result is True
        assert sample_task.is_deleted is True
        task_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, task_service, nonexistent_object_id):
        """Test suppression d'une tâche inexistante."""
        # Arrange
        task_service.engine.find_one.return_value = None

        # Act
        result = await task_service.delete_task(nonexistent_object_id)

        # Assert
        assert result is False


class TestTaskServiceConstants:
    """Tests pour les méthodes de constantes."""

    @pytest.mark.asyncio
    async def test_get_task_type_list(self, task_service):
        """Test récupération de la liste des types de tâches."""
        # Act
        result = await task_service.get_task_type_list()

        # Assert
        assert isinstance(result, dict)
        assert "BUG" in result
        assert "TASK" in result
        assert "STORY" in result
        assert result["BUG"] == "Bug"
        assert result["TASK"] == "Task"

    @pytest.mark.asyncio
    async def test_get_task_status_list(self, task_service):
        """Test récupération de la liste des statuts de tâches."""
        # Act
        result = await task_service.get_task_status_list()

        # Assert
        assert isinstance(result, dict)
        assert "TODO" in result
        assert "PROG" in result
        assert "DONE" in result
        assert result["TODO"] == "To do"
        assert result["PROG"] == "In progress"

    @pytest.mark.asyncio
    async def test_get_delivery_status_list(self, task_service):
        """Test récupération de la liste des statuts de livraison."""
        # Act
        result = await task_service.get_delivery_status_list()

        # Assert
        assert isinstance(result, dict)
        assert "" in result
        assert "OK" in result
        assert "KO" in result
        assert result[""] == "Not set"
        assert result["OK"] == "Delivered successfully"
        assert result["KO"] == "Delivery issue"