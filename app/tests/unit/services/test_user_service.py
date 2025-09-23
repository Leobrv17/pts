"""Tests unitaires pour UserService."""

import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from fastapi import HTTPException

from app.models.user import User, UserTypeEnum, DirectorAccess, ProjectAccess, AccessLevelEnum
from app.models.service_center import ServiceCenter, ServiceCenterStatus
from app.models.project import Project, ProjectStatus
from app.schemas.user import (
    UserCreate, UserLite, DirectorAccessBase, ProjectAccessBase
)


class TestUserServiceCreate:
    """Tests pour la création d'utilisateurs."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service):
        """Test création réussie d'un utilisateur."""
        # Arrange
        user_data = UserCreate(
            firstName="John",
            familyName="Doe",
            email="john.doe@sii.fr",
            type=UserTypeEnum.NORMAL,
            registrationNumber="123456",
            trigram="JDO"
        )

        # Act
        result = await user_service.create_user(user_data)

        # Assert
        assert result.first_name == user_data.firstName
        assert result.family_name == user_data.familyName
        assert result.email == user_data.email
        assert result.type == user_data.type
        assert result.registration_number == user_data.registrationNumber
        assert result.trigram == user_data.trigram
        assert result.director_access_list == []
        assert result.project_access_list == []
        user_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_minimal_data(self, user_service):
        """Test création avec données minimales."""
        # Arrange
        user_data = UserCreate(
            firstName="Jane",
            familyName="Smith",
            email="jane.smith@sii.fr",
            trigram="JSM"
        )

        # Act
        result = await user_service.create_user(user_data)

        # Assert
        assert result.first_name == "Jane"
        assert result.family_name == "Smith"
        assert result.type == UserTypeEnum.NORMAL
        assert result.registration_number == ""
        user_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_database_error(self, user_service):
        """Test gestion d'erreur lors de la création."""
        # Arrange
        user_data = UserCreate(
            firstName="Error",
            familyName="User",
            email="error@sii.fr",
            trigram="ERR"
        )
        user_service.engine.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(user_data)

        assert exc_info.value.status_code == 400
        assert "Error creating user" in exc_info.value.detail


class TestUserServiceRead:
    """Tests pour la lecture d'utilisateurs."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, sample_user):
        """Test récupération réussie d'un utilisateur par ID."""
        # Arrange
        user_service.engine.find_one.return_value = sample_user

        # Act
        result = await user_service.get_user_by_id(str(sample_user.id))

        # Assert
        assert result == sample_user
        user_service.engine.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, nonexistent_object_id):
        """Test récupération d'un utilisateur inexistant."""
        # Arrange
        user_service.engine.find_one.return_value = None

        # Act
        result = await user_service.get_user_by_id(nonexistent_object_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_id(self, user_service, invalid_object_id):
        """Test récupération avec un ID invalide."""
        # Act
        result = await user_service.get_user_by_id(invalid_object_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_users_by_ids_success(self, user_service, sample_user):
        """Test récupération de plusieurs utilisateurs par IDs."""
        # Arrange
        user_ids = [str(sample_user.id)]
        user_service.engine.find.return_value = [sample_user]

        # Act
        result = await user_service.get_users_by_ids(user_ids)

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user
        user_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_users_by_ids_empty_list(self, user_service):
        """Test récupération avec une liste vide d'IDs."""
        # Arrange
        user_service.engine.find.return_value = []

        # Act
        result = await user_service.get_users_by_ids([])

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_users_with_pagination(self, user_service, sample_user):
        """Test récupération avec pagination."""
        # Arrange
        users_list = [sample_user]
        user_service.engine.find.return_value = users_list
        user_service.engine.count.return_value = 1

        # Act
        users, total = await user_service.get_users(skip=0, limit=10)

        # Assert
        assert len(users) == 1
        assert total == 1
        assert users[0] == sample_user

    @pytest.mark.asyncio
    async def test_get_users_with_name_filter(self, user_service, sample_user):
        """Test récupération avec filtre de nom."""
        # Arrange
        user_service.engine.find.return_value = [sample_user]
        user_service.engine.count.return_value = 1

        # Act
        users, total = await user_service.get_users(name_substring="John")

        # Assert
        assert len(users) == 1
        assert total == 1
        user_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_users_by_name_success(self, user_service, sample_user):
        """Test récupération d'utilisateurs par nom."""
        # Arrange
        user_service.engine.find.return_value = [sample_user]
        user_service.engine.count.return_value = 1

        # Act
        result = await user_service.get_users_by_name("John")

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    @pytest.mark.asyncio
    async def test_get_users_by_name_no_substring(self, user_service, sample_user):
        """Test récupération sans substring."""
        # Arrange
        user_service.engine.find.return_value = [sample_user]
        user_service.engine.count.return_value = 1

        # Act
        result = await user_service.get_users_by_name()

        # Assert
        assert len(result) == 1


class TestUserServiceUpdate:
    """Tests pour la mise à jour d'utilisateurs."""

    @pytest.mark.asyncio
    async def test_update_user_lite_success(self, user_service, sample_user, sample_service_center):
        """Test mise à jour réussie avec UserLite."""
        # Arrange
        user_service.engine.find_one.side_effect = [
            sample_user,  # get_user_by_id
            sample_service_center  # _get_service_center_name
        ]

        user_lite = UserLite(
            id=str(sample_user.id),
            firstName="John Updated",
            familyName="Doe Updated",
            email="john.updated@sii.fr",
            type=UserTypeEnum.ADMIN,
            registrationNumber="789123",
            trigram="JUD",
            directorAccessList=[DirectorAccessBase(serviceCenterId=str(sample_service_center.id))],
            projectAccessList=[]
        )

        with patch.object(user_service, '_manage_director_accesses_with_id_logic') as mock_director:
            with patch.object(user_service, '_manage_project_accesses_with_id_logic') as mock_project:
                # Act
                result = await user_service.update_user_lite(user_lite)

                # Assert
                assert result.first_name == "John Updated"
                assert result.family_name == "Doe Updated"
                assert result.email == "john.updated@sii.fr"
                assert result.type == UserTypeEnum.ADMIN
                mock_director.assert_called_once()
                mock_project.assert_called_once()
                user_service.engine.save.assert_called()

    @pytest.mark.asyncio
    async def test_update_user_lite_not_found(self, user_service, nonexistent_object_id):
        """Test mise à jour d'un utilisateur inexistant."""
        # Arrange
        user_service.engine.find_one.return_value = None

        user_lite = UserLite(
            id=nonexistent_object_id,
            firstName="Not Found",
            familyName="User",
            email="notfound@sii.fr",
            trigram="NFU"
        )

        # Act
        result = await user_service.update_user_lite(user_lite)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_lite_with_access_management(self, user_service, sample_user):
        """Test mise à jour avec gestion des accès."""
        # Arrange
        user_service.engine.find_one.return_value = sample_user

        user_lite = UserLite(
            id=str(sample_user.id),
            firstName="John",
            familyName="Doe",
            email="john.doe@sii.fr",
            trigram="JDO",
            directorAccessList=None,
            projectAccessList=None
        )

        # Act
        with patch.object(user_service, '_manage_director_accesses_with_id_logic') as mock_director:
            with patch.object(user_service, '_manage_project_accesses_with_id_logic') as mock_project:
                await user_service.update_user_lite(user_lite)

                # Assert
                mock_director.assert_not_called()
                mock_project.assert_not_called()


class TestUserServiceDelete:
    """Tests pour la suppression d'utilisateurs."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, sample_user):
        """Test suppression réussie d'un utilisateur."""
        # Arrange
        user_service.engine.find_one.return_value = sample_user
        sample_user.is_deleted = False

        # Act
        result = await user_service.delete_user(str(sample_user.id))

        # Assert
        assert result is True
        assert sample_user.is_deleted is True
        user_service.engine.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, nonexistent_object_id):
        """Test suppression d'un utilisateur inexistant."""
        # Arrange
        user_service.engine.find_one.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user(nonexistent_object_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail


class TestUserServiceAccessManagement:
    """Tests pour la gestion des accès."""

    @pytest.mark.asyncio
    async def test_get_director_access_by_user_success(self, user_service, sample_user, sample_director_access):
        """Test récupération des accès directeur par utilisateur."""
        # Arrange
        user_service.engine.find.return_value = [sample_director_access]
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")

        # Act
        result = await user_service.get_director_access_by_user(str(sample_user.id))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_director_access
        user_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_director_access_by_user_empty(self, user_service, sample_user):
        """Test récupération sans accès directeur."""
        # Arrange
        user_service.engine.find.return_value = []

        # Act
        result = await user_service.get_director_access_by_user(str(sample_user.id))

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_project_access_by_user_success(self, user_service, sample_user, sample_project_access):
        """Test récupération des accès projet par utilisateur."""
        # Arrange
        user_service.engine.find.return_value = [sample_project_access]
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")
        user_service._get_project_name = AsyncMock(return_value="Test Project")

        # Act
        result = await user_service.get_project_access_by_user(str(sample_user.id))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_project_access
        user_service.engine.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_accesses_by_project_success(self, user_service, sample_project, sample_project_access):
        """Test récupération des accès projet par projet."""
        # Arrange
        user_service.engine.find.return_value = [sample_project_access]
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")
        user_service._get_project_name = AsyncMock(return_value="Test Project")

        # Act
        result = await user_service.get_project_accesses_by_project(str(sample_project.id))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_project_access

    @pytest.mark.asyncio
    async def test_get_director_accesses_by_service_center_success(self, user_service, sample_service_center, sample_director_access):
        """Test récupération des accès directeur par centre de service."""
        # Arrange
        user_service.engine.find.return_value = [sample_director_access]
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")

        # Act
        result = await user_service.get_director_accesses_by_service_center(str(sample_service_center.id))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_director_access

    @pytest.mark.asyncio
    async def test_get_project_accesses_by_service_center_success(self, user_service, sample_service_center, sample_project_access):
        """Test récupération des accès projet par centre de service."""
        # Arrange
        user_service.engine.find.return_value = [sample_project_access]
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")
        user_service._get_project_name = AsyncMock(return_value="Test Project")

        # Act
        result = await user_service.get_project_accesses_by_service_center(str(sample_service_center.id))

        # Assert
        assert len(result) == 1
        assert result[0] == sample_project_access


class TestUserServiceUtilityMethods:
    """Tests pour les méthodes utilitaires."""

    @pytest.mark.asyncio
    async def test_get_service_center_name_success(self, user_service, sample_service_center):
        """Test récupération du nom de centre de service."""
        # Arrange
        user_service.engine.find_one.return_value = sample_service_center

        # Act
        result = await user_service._get_service_center_name(sample_service_center.id)

        # Assert
        assert result == sample_service_center.centerName

    @pytest.mark.asyncio
    async def test_get_service_center_name_not_found(self, user_service, valid_object_id):
        """Test récupération d'un nom de centre inexistant."""
        # Arrange
        user_service.engine.find_one.return_value = None

        # Act
        result = await user_service._get_service_center_name(valid_object_id)

        # Assert
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_project_name_success(self, user_service, sample_project):
        """Test récupération du nom de projet."""
        # Arrange
        user_service.engine.find_one.return_value = sample_project

        # Act
        result = await user_service._get_project_name(sample_project.id)

        # Assert
        assert result == sample_project.projectName

    @pytest.mark.asyncio
    async def test_get_project_name_not_found(self, user_service, valid_object_id):
        """Test récupération d'un nom de projet inexistant."""
        # Arrange
        user_service.engine.find_one.return_value = None

        # Act
        result = await user_service._get_project_name(valid_object_id)

        # Assert
        assert result == ""

    @pytest.mark.asyncio
    async def test_populate_access_names_success(self, user_service, sample_director_access):
        """Test population des noms d'accès directeur."""
        # Arrange
        sample_director_access.service_center_name = ""
        user_service._get_service_center_name = AsyncMock(return_value="Updated Center Name")

        # Act
        result = await user_service._populate_access_names([sample_director_access])

        # Assert
        assert len(result) == 1
        assert result[0].service_center_name == "Updated Center Name"

    @pytest.mark.asyncio
    async def test_populate_project_access_names_success(self, user_service, sample_project_access):
        """Test population des noms d'accès projet."""
        # Arrange
        sample_project_access.service_center_name = ""
        sample_project_access.project_name = ""
        user_service._get_service_center_name = AsyncMock(return_value="Updated Center Name")
        user_service._get_project_name = AsyncMock(return_value="Updated Project Name")

        # Act
        result = await user_service._populate_project_access_names([sample_project_access])

        # Assert
        assert len(result) == 1
        assert result[0].service_center_name == "Updated Center Name"
        assert result[0].project_name == "Updated Project Name"


class TestUserServiceFieldMapping:
    """Tests pour le mapping des champs."""

    def test_map_camelcase_to_snake_success(self, user_service):
        """Test mapping CamelCase vers snake_case."""
        # Arrange
        user_data = UserCreate(
            firstName="Test",
            familyName="User",
            email="test@sii.fr",
            type=UserTypeEnum.NORMAL,
            registrationNumber="123",
            trigram="TST"
        )

        # Act
        result = user_service._map_camelcase_to_snake(user_data)

        # Assert
        expected = {
            'first_name': 'Test',
            'family_name': 'User',
            'email': 'test@sii.fr',
            'type': UserTypeEnum.NORMAL,
            'registration_number': '123',
            'trigram': 'TST',
            'director_access_list': [],
            'project_access_list': []
        }
        assert result == expected

    def test_map_user_lite_to_snake_success(self, user_service, valid_object_id):
        """Test mapping UserLite vers snake_case."""
        # Arrange
        user_lite = UserLite(
            id=str(valid_object_id),
            firstName="Test",
            familyName="User",
            email="test@sii.fr",
            trigram="TST"
        )

        # Act
        result = user_service._map_user_lite_to_snake(user_lite)

        # Assert
        expected = {
            'first_name': 'Test',
            'family_name': 'User',
            'email': 'test@sii.fr',
            'type': UserTypeEnum.NORMAL,  # Default value
            'registration_number': '',
            'trigram': 'TST'
        }
        assert result == expected


class TestUserServiceAccessIdLogic:
    """Tests pour la logique de gestion des accès avec IDs."""

    @pytest.mark.asyncio
    async def test_manage_director_accesses_with_new_access(self, user_service, sample_user, sample_service_center):
        """Test gestion des accès directeur avec nouvel accès."""
        # Arrange
        user_service.engine.find.return_value = []  # Pas d'accès existant
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")

        director_accesses = [DirectorAccessBase(serviceCenterId=str(sample_service_center.id))]

        # Act
        await user_service._manage_director_accesses_with_id_logic(sample_user, director_accesses)

        # Assert
        user_service.engine.save.assert_called()  # Pour créer le nouvel accès

    @pytest.mark.asyncio
    async def test_manage_director_accesses_with_existing_access(self, user_service, sample_user, sample_director_access):
        """Test gestion des accès directeur avec mise à jour d'un accès existant."""
        # Arrange
        user_service.engine.find_one.return_value = sample_director_access
        user_service.engine.find.return_value = [sample_director_access]
        user_service._get_service_center_name = AsyncMock(return_value="Updated Center")

        director_accesses = [DirectorAccessBase(
            id=str(sample_director_access.id),
            serviceCenterId=str(sample_director_access.service_center_id)
        )]

        # Act
        await user_service._manage_director_accesses_with_id_logic(sample_user, director_accesses)

        # Assert
        user_service.engine.save.assert_called()  # Pour mettre à jour l'accès

    @pytest.mark.asyncio
    async def test_manage_project_accesses_with_new_access(self, user_service, sample_user, sample_service_center, sample_project):
        """Test gestion des accès projet avec nouvel accès."""
        # Arrange
        user_service.engine.find.return_value = []  # Pas d'accès existant
        user_service._get_service_center_name = AsyncMock(return_value="Test Center")
        user_service._get_project_name = AsyncMock(return_value="Test Project")

        project_accesses = [ProjectAccessBase(
            serviceCenterId=str(sample_service_center.id),
            projectId=str(sample_project.id),
            accessLevel=AccessLevelEnum.TEAM_MEMBER,
            occupancyRate=50.0
        )]

        # Act
        await user_service._manage_project_accesses_with_id_logic(sample_user, project_accesses)

        # Assert
        user_service.engine.save.assert_called()  # Pour créer le nouvel accès

    @pytest.mark.asyncio
    async def test_manage_project_accesses_with_invalid_id(self, user_service, sample_user, valid_object_id):
        """Test gestion des accès projet avec ID invalide."""
        # Arrange
        user_service.engine.find_one.return_value = None

        project_accesses = [ProjectAccessBase(
            id="invalid_id",
            serviceCenterId=str(valid_object_id),
            projectId=str(valid_object_id),
            accessLevel=AccessLevelEnum.TEAM_MEMBER,
            occupancyRate=50.0
        )]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service._manage_project_accesses_with_id_logic(sample_user, project_accesses)

        assert exc_info.value.status_code == 400
        assert "Invalid project access ID" in exc_info.value.detail