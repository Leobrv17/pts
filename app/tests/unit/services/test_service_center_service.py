"""Tests unitaires pour ServiceCenterService."""

import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from fastapi import HTTPException

from app.models.service_center import ServiceCenter, ServiceCenterStatus
from app.schemas.service_center import ServiceCenterBase, ServiceCenterUpdate


class TestServiceCenterServiceCreate:
    """Tests pour la création de centres de service."""

    @pytest.mark.asyncio
    async def test_create_service_center_success(self, service_center_service):
        """Test création réussie d'un centre de service."""
        # Arrange
        center_data = ServiceCenterBase(
            centerName="New Service Center",
            location="Paris, France",
            contactEmail="contact@paris.sii.fr",
            contactPhone="0123456789",
            status=ServiceCenterStatus.OPERATIONAL
        )

        # Act
        result = await service_center_service.create_service_center(center_data)

        # Assert
        assert result.centerName == center_data.centerName
        assert result.location == center_data.location
        assert result.contactEmail == center_data.contactEmail
        assert result.contactPhone == center_data.contactPhone
        assert result.status == center_data.status
        assert result.projects == []
        assert result.users == []
        assert result.transversal_activities == []
        assert result.possible_task_statuses == {}
        assert result.possible_task_types == {}
        service_center_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_service_center_minimal_data(self, service_center_service):
        """Test création avec données minimales."""
        # Arrange
        center_data = ServiceCenterBase(
            centerName="Minimal Center"
        )

        # Act
        result = await service_center_service.create_service_center(center_data)

        # Assert
        assert result.centerName == "Minimal Center"
        assert result.location == ""
        assert result.contactEmail is None
        assert result.contactPhone == ""
        assert result.status == ServiceCenterStatus.OPERATIONAL
        service_center_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_service_center_with_empty_email(self, service_center_service):
        """Test création avec email vide."""
        # Arrange
        center_data = ServiceCenterBase(
            centerName="Center With Empty Email",
            contactEmail=""  # Email vide qui sera converti en None par le validator
        )

        # Act
        result = await service_center_service.create_service_center(center_data)

        # Assert
        assert result.contactEmail is None
        service_center_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_service_center_database_error(self, service_center_service):
        """Test gestion d'erreur lors de la création."""
        # Arrange
        center_data = ServiceCenterBase(
            centerName="Failed Center"
        )
        service_center_service.engine.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service_center_service.create_service_center(center_data)

        assert exc_info.value.status_code == 400
        assert "Error creating service center" in exc_info.value.detail


class TestServiceCenterServiceRead:
    """Tests pour la lecture de centres de service."""

    @pytest.mark.asyncio
    async def test_get_service_center_by_id_success(self, service_center_service, sample_service_center):
        """Test récupération réussie d'un centre par ID."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center

        # Act
        result = await service_center_service.get_service_center_by_id(str(sample_service_center.id))

        # Assert
        assert result == sample_service_center
        service_center_service.engine.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_service_center_by_id_not_found(self, service_center_service, nonexistent_object_id):
        """Test récupération d'un centre inexistant."""
        # Arrange
        service_center_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service_center_service.get_service_center_by_id(nonexistent_object_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_service_center_by_id_invalid_id(self, service_center_service, invalid_object_id):
        """Test récupération avec un ID invalide."""
        # Act
        result = await service_center_service.get_service_center_by_id(invalid_object_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_service_center_by_id_with_deleted_flag(self, service_center_service, sample_service_center):
        """Test récupération avec flag is_deleted."""
        # Arrange
        sample_service_center.is_deleted = True
        service_center_service.engine.find_one.return_value = sample_service_center

        # Act
        result = await service_center_service.get_service_center_by_id(
            str(sample_service_center.id),
            is_deleted=True
        )

        # Assert
        assert result == sample_service_center

    @pytest.mark.asyncio
    async def test_get_service_centers_success(self, service_center_service):
        """Test récupération de tous les centres."""
        # Arrange
        centers = [
            ServiceCenter(
                id=ObjectId(),
                centerName="Center 1",
                status=ServiceCenterStatus.OPERATIONAL,
                projects=[],
                users=[],
                transversal_activities=[],
                possible_task_statuses={},
                possible_task_types={}
            ),
            ServiceCenter(
                id=ObjectId(),
                centerName="Center 2",
                status=ServiceCenterStatus.CLOSED,
                projects=[],
                users=[],
                transversal_activities=[],
                possible_task_statuses={},
                possible_task_types={}
            )
        ]
        service_center_service.engine.find.return_value = centers
        service_center_service.engine.count.return_value = len(centers)

        # Act
        result_centers, total = await service_center_service.get_service_centers()

        # Assert
        assert len(result_centers) == 2
        assert total == 2
        service_center_service.engine.find.assert_called_once()
        service_center_service.engine.count.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_service_centers_with_status_filter(self, service_center_service):
        """Test récupération avec filtre de statut."""
        # Arrange
        operational_centers = [
            ServiceCenter(
                id=ObjectId(),
                centerName="Operational Center",
                status=ServiceCenterStatus.OPERATIONAL,
                projects=[],
                users=[],
                transversal_activities=[],
                possible_task_statuses={},
                possible_task_types={}
            )
        ]
        service_center_service.engine.find.return_value = operational_centers
        service_center_service.engine.count.return_value = 1

        # Act
        result_centers, total = await service_center_service.get_service_centers(
            status="Operational"
        )

        # Assert
        assert len(result_centers) == 1
        assert total == 1
        assert result_centers[0].status == ServiceCenterStatus.OPERATIONAL

    @pytest.mark.asyncio
    async def test_get_service_centers_with_pagination(self, service_center_service):
        """Test récupération avec pagination."""
        # Arrange
        centers = [ServiceCenter(
            id=ObjectId(),
            centerName=f"Center {i}",
            status=ServiceCenterStatus.OPERATIONAL,
            projects=[],
            users=[],
            transversal_activities=[],
            possible_task_statuses={},
            possible_task_types={}
        ) for i in range(5)]

        service_center_service.engine.find.return_value = centers[:3]  # Page 1, size 3
        service_center_service.engine.count.return_value = 5

        # Act
        result_centers, total = await service_center_service.get_service_centers(
            skip=0,
            limit=3
        )

        # Assert
        assert len(result_centers) == 3
        assert total == 5

    @pytest.mark.asyncio
    async def test_get_service_centers_with_deleted_filter(self, service_center_service):
        """Test récupération avec filtre is_deleted."""
        # Arrange
        deleted_centers = [ServiceCenter(
            id=ObjectId(),
            centerName="Deleted Center",
            status=ServiceCenterStatus.CLOSED,
            is_deleted=True,
            projects=[],
            users=[],
            transversal_activities=[],
            possible_task_statuses={},
            possible_task_types={}
        )]
        service_center_service.engine.find.return_value = deleted_centers
        service_center_service.engine.count.return_value = 1

        # Act
        result_centers, total = await service_center_service.get_service_centers(
            is_deleted=True
        )

        # Assert
        assert len(result_centers) == 1
        assert total == 1


class TestServiceCenterServiceUpdate:
    """Tests pour la mise à jour de centres de service."""

    @pytest.mark.asyncio
    async def test_update_service_center_success(self, service_center_service, sample_service_center):
        """Test mise à jour réussie d'un centre."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center

        update_data = ServiceCenterUpdate(
            id=str(sample_service_center.id),
            centerName="Updated Center Name",
            location="Updated Location",
            contactEmail="updated@sii.fr",
            status=ServiceCenterStatus.CLOSED
        )

        # Act
        result = await service_center_service.update_service_center(update_data)

        # Assert
        assert result.centerName == "Updated Center Name"
        assert result.location == "Updated Location"
        assert result.contactEmail == "updated@sii.fr"
        assert result.status == ServiceCenterStatus.CLOSED
        service_center_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_service_center_partial(self, service_center_service, sample_service_center):
        """Test mise à jour partielle."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center
        original_location = sample_service_center.location

        update_data = ServiceCenterUpdate(
            id=str(sample_service_center.id),
            centerName="Only Name Updated"
        )

        # Act
        result = await service_center_service.update_service_center(update_data)

        # Assert
        assert result.centerName == "Only Name Updated"
        assert result.location == original_location  # Pas changé
        service_center_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_service_center_not_found(self, service_center_service, nonexistent_object_id):
        """Test mise à jour d'un centre inexistant."""
        # Arrange
        service_center_service.engine.find_one.return_value = None

        update_data = ServiceCenterUpdate(
            id=nonexistent_object_id,
            centerName="Won't be updated"
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await service_center_service.update_service_center(update_data)

    @pytest.mark.asyncio
    async def test_update_service_center_database_error(self, service_center_service, sample_service_center):
        """Test gestion d'erreur lors de la mise à jour."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center
        service_center_service.engine.save.side_effect = Exception("Database error")

        update_data = ServiceCenterUpdate(
            id=str(sample_service_center.id),
            centerName="Error Center"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service_center_service.update_service_center(update_data)

        assert exc_info.value.status_code == 400
        assert "Error updating service center" in exc_info.value.detail


class TestServiceCenterServiceDelete:
    """Tests pour la suppression de centres de service."""

    @pytest.mark.asyncio
    async def test_delete_service_center_success(self, service_center_service, sample_service_center):
        """Test suppression réussie d'un centre."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center
        sample_service_center.is_deleted = False

        # Act
        result = await service_center_service.delete_service_center(str(sample_service_center.id))

        # Assert
        assert result is True
        assert sample_service_center.is_deleted is True
        service_center_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_service_center_not_found(self, service_center_service, nonexistent_object_id):
        """Test suppression d'un centre inexistant."""
        # Arrange
        service_center_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException):
            await service_center_service.delete_service_center(nonexistent_object_id)

    @pytest.mark.asyncio
    async def test_delete_service_center_already_deleted(self, service_center_service, sample_service_center):
        """Test suppression d'un centre déjà supprimé."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center
        sample_service_center.is_deleted = True

        # Act
        result = await service_center_service.delete_service_center(str(sample_service_center.id))

        # Assert
        assert result is True
        assert sample_service_center.is_deleted is True
        service_center_service.engine.save.assert_called_once()


class TestServiceCenterServiceFieldMapping:
    """Tests pour le mapping des champs."""

    @pytest.mark.asyncio
    async def test_field_mapping_completeness(self, service_center_service, sample_service_center):
        """Test que tous les champs sont bien mappés."""
        # Arrange
        service_center_service.engine.find_one.return_value = sample_service_center

        update_data = ServiceCenterUpdate(
            id=str(sample_service_center.id),
            centerName="Mapped Center",
            location="Mapped Location",
            contactEmail="mapped@sii.fr",
            contactPhone="0987654321",
            status=ServiceCenterStatus.CLOSED
        )

        # Act
        result = await service_center_service.update_service_center(update_data)

        # Assert
        # Vérifier que tous les champs du mapping sont appliqués
        for schema_field, model_field in service_center_service._field_mapping.items():
            if hasattr(update_data, schema_field) and getattr(update_data, schema_field) is not None:
                assert hasattr(result, model_field)
                assert getattr(result, model_field) == getattr(update_data, schema_field)