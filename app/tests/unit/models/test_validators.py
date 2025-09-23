"""Tests unitaires pour les validators des modèles."""

import pytest
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import ValidationError

from app.models.user import User, UserTypeEnum, DirectorAccess, ProjectAccess, AccessLevelEnum
from app.models.service_center import ServiceCenter, ServiceCenterStatus
from app.models.project import Project, ProjectStatus, ProjectTransversalActivity
from app.models.sprint import Sprint, SprintStatus, SprintTransversalActivity
from app.models.task import Task, TaskStatus, TaskType, TASKRFT, TaskDeliveryStatus


class TestUserModelValidators:
    """Tests pour les validators du modèle User."""

    def test_user_creation_valid_data(self):
        """Test création d'un utilisateur avec des données valides."""
        # Act
        user = User(
            first_name="John",
            family_name="Doe",
            email="john.doe@sii.fr",
            type=UserTypeEnum.NORMAL,
            registration_number="123456",
            trigram="JDO"
        )

        # Assert
        assert user.first_name == "John"
        assert user.family_name == "Doe"
        assert user.email == "john.doe@sii.fr"
        assert user.type == UserTypeEnum.NORMAL
        assert user.trigram == "JDO"
        assert user.director_access_list == []
        assert user.project_access_list == []
        assert user.is_deleted is False

    def test_user_creation_minimal_data(self):
        """Test création avec données minimales."""
        # Act
        user = User(
            first_name="Jane",
            family_name="Smith",
            email="jane.smith@sii.fr",
            trigram="JSM"
        )

        # Assert
        assert user.first_name == "Jane"
        assert user.family_name == "Smith"
        assert user.type == UserTypeEnum.NORMAL  # Valeur par défaut
        assert user.registration_number == ""  # Valeur par défaut
        assert user.trigram == "JSM"

    def test_user_trigram_validation_valid(self):
        """Test validation du trigram valide."""
        # Act & Assert - Ne doit pas lever d'exception
        user = User(
            first_name="Test",
            family_name="User",
            email="test@sii.fr",
            trigram="ABC"
        )
        assert user.trigram == "ABC"

    def test_user_trigram_validation_invalid_length(self):
        """Test validation du trigram avec longueur invalide."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="Test",
                family_name="User",
                email="test@sii.fr",
                trigram="AB"  # Trop court
            )

        error_messages = str(exc_info.value)
        assert "at least 3 characters" in error_messages

    def test_user_trigram_validation_too_long(self):
        """Test validation du trigram trop long."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="Test",
                family_name="User",
                email="test@sii.fr",
                trigram="ABCD"  # Trop long
            )

        error_messages = str(exc_info.value)
        assert "at most 3 characters" in error_messages

    def test_user_email_validation_valid(self):
        """Test validation d'email valide."""
        # Act & Assert - Ne doit pas lever d'exception
        user = User(
            first_name="Test",
            family_name="User",
            email="valid.email@example.com",
            trigram="TST"
        )
        assert user.email == "valid.email@example.com"

    def test_user_email_validation_invalid(self):
        """Test validation d'email invalide."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="Test",
                family_name="User",
                email="invalid-email",  # Email invalide
                trigram="TST"
            )

        error_messages = str(exc_info.value)
        assert "value is not a valid email address" in error_messages

    def test_user_name_validation_empty_first_name(self):
        """Test validation avec prénom vide."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="",  # Prénom vide
                family_name="User",
                email="test@sii.fr",
                trigram="TST"
            )

        error_messages = str(exc_info.value)
        assert "at least 1 character" in error_messages

    def test_user_name_validation_empty_family_name(self):
        """Test validation avec nom de famille vide."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="Test",
                family_name="",  # Nom vide
                email="test@sii.fr",
                trigram="TST"
            )

        error_messages = str(exc_info.value)
        assert "at least 1 character" in error_messages

    def test_user_name_validation_too_long(self):
        """Test validation avec noms trop longs."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="A" * 101,  # Trop long (max 100)
                family_name="User",
                email="test@sii.fr",
                trigram="TST"
            )

        error_messages = str(exc_info.value)
        assert "at most 100 characters" in error_messages

    def test_user_registration_number_validation_too_long(self):
        """Test validation du numéro d'enregistrement trop long."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            User(
                first_name="Test",
                family_name="User",
                email="test@sii.fr",
                trigram="TST",
                registration_number="A" * 51  # Trop long (max 50)
            )

        error_messages = str(exc_info.value)
        assert "at most 50 characters" in error_messages

    def test_user_defaults(self):
        """Test des valeurs par défaut."""
        # Act
        user = User(
            first_name="Test",
            family_name="User",
            email="test@sii.fr",
            trigram="TST"
        )

        # Assert
        assert user.type == UserTypeEnum.NORMAL
        assert user.registration_number == ""
        assert user.director_access_list == []
        assert user.project_access_list == []
        assert isinstance(user.created_at, datetime)
        assert user.is_deleted is False


class TestDirectorAccessValidators:
    """Tests pour les validators du modèle DirectorAccess."""

    def test_director_access_creation_valid(self, valid_object_id, another_object_id):
        """Test création d'un accès directeur valide."""
        # Act
        access = DirectorAccess(
            user_id=valid_object_id,
            service_center_id=another_object_id,
            service_center_name="Test Center"
        )

        # Assert
        assert access.user_id == valid_object_id
        assert access.service_center_id == another_object_id
        assert access.service_center_name == "Test Center"
        assert isinstance(access.created_at, datetime)
        assert access.is_deleted is False

    def test_director_access_defaults(self, valid_object_id, another_object_id):
        """Test des valeurs par défaut."""
        # Act
        access = DirectorAccess(
            user_id=valid_object_id,
            service_center_id=another_object_id,
            service_center_name="Test Center"
        )

        # Assert
        assert isinstance(access.created_at, datetime)
        assert access.is_deleted is False


class TestProjectAccessValidators:
    """Tests pour les validators du modèle ProjectAccess."""

    def test_project_access_creation_valid(self, valid_object_id, another_object_id):
        """Test création d'un accès projet valide."""
        # Act
        access = ProjectAccess(
            user_id=valid_object_id,
            service_center_id=another_object_id,
            service_center_name="Test Center",
            project_id=ObjectId(),
            project_name="Test Project",
            access_level=AccessLevelEnum.TEAM_MEMBER,
            occupancy_rate=50.0
        )

        # Assert
        assert access.user_id == valid_object_id
        assert access.service_center_id == another_object_id
        assert access.project_name == "Test Project"
        assert access.access_level == AccessLevelEnum.TEAM_MEMBER
        assert access.occupancy_rate == 50.0

    def test_project_access_occupancy_rate_validation_valid(self, valid_object_id, another_object_id):
        """Test validation du taux d'occupation valide."""
        # Act & Assert - Ne doit pas lever d'exception
        access = ProjectAccess(
            user_id=valid_object_id,
            service_center_id=another_object_id,
            service_center_name="Test Center",
            project_id=ObjectId(),
            project_name="Test Project",
            access_level=AccessLevelEnum.TEAM_MEMBER,
            occupancy_rate=100.0  # Maximum valide
        )
        assert access.occupancy_rate == 100.0

    def test_project_access_occupancy_rate_validation_too_high(self, valid_object_id, another_object_id):
        """Test validation du taux d'occupation trop élevé."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProjectAccess(
                user_id=valid_object_id,
                service_center_id=another_object_id,
                service_center_name="Test Center",
                project_id=ObjectId(),
                project_name="Test Project",
                access_level=AccessLevelEnum.TEAM_MEMBER,
                occupancy_rate=101.0  # Trop élevé
            )

        error_messages = str(exc_info.value)
        assert "less than or equal to 100" in error_messages

    def test_project_access_occupancy_rate_validation_negative(self, valid_object_id, another_object_id):
        """Test validation du taux d'occupation négatif."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProjectAccess(
                user_id=valid_object_id,
                service_center_id=another_object_id,
                service_center_name="Test Center",
                project_id=ObjectId(),
                project_name="Test Project",
                access_level=AccessLevelEnum.TEAM_MEMBER,
                occupancy_rate=-1.0  # Négatif
            )

        error_messages = str(exc_info.value)
        assert "greater than or equal to 0" in error_messages

    def test_project_access_defaults(self, valid_object_id, another_object_id):
        """Test des valeurs par défaut."""
        # Act
        access = ProjectAccess(
            user_id=valid_object_id,
            service_center_id=another_object_id,
            service_center_name="Test Center",
            project_id=ObjectId(),
            project_name="Test Project",
            access_level=AccessLevelEnum.TEAM_MEMBER
        )

        # Assert
        assert access.occupancy_rate == 0.0  # Valeur par défaut
        assert isinstance(access.created_at, datetime)
        assert access.is_deleted is False


class TestServiceCenterValidators:
    """Tests pour les validators du modèle ServiceCenter."""

    def test_service_center_creation_valid(self):
        """Test création d'un centre de service valide."""
        # Act
        center = ServiceCenter(
            centerName="Test Center",
            location="Toulouse, France",
            contactEmail="contact@sii.fr",
            contactPhone="0123456789",
            status=ServiceCenterStatus.OPERATIONAL
        )

        # Assert
        assert center.centerName == "Test Center"
        assert center.location == "Toulouse, France"
        assert center.contactEmail == "contact@sii.fr"
        assert center.contactPhone == "0123456789"
        assert center.status == ServiceCenterStatus.OPERATIONAL

    def test_service_center_creation_minimal(self):
        """Test création avec données minimales."""
        # Act
        center = ServiceCenter(
            centerName="Minimal Center"
        )

        # Assert
        assert center.centerName == "Minimal Center"
        assert center.location == ""  # Valeur par défaut
        assert center.contactEmail is None  # Valeur par défaut
        assert center.contactPhone == ""  # Valeur par défaut
        assert center.status == ServiceCenterStatus.OPERATIONAL  # Valeur par défaut

    def test_service_center_name_validation_empty(self):
        """Test validation avec nom vide."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ServiceCenter(
                centerName=""  # Nom vide
            )

        error_messages = str(exc_info.value)
        assert "at least 1 character" in error_messages

    def test_service_center_name_validation_too_long(self):
        """Test validation avec nom trop long."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ServiceCenter(
                centerName="A" * 201  # Trop long (max 200)
            )

        error_messages = str(exc_info.value)
        assert "at most 200 characters" in error_messages

    def test_service_center_email_validation_valid(self):
        """Test validation d'email valide."""
        # Act & Assert - Ne doit pas lever d'exception
        center = ServiceCenter(
            centerName="Test Center",
            contactEmail="valid@example.com"
        )
        assert center.contactEmail == "valid@example.com"

    def test_service_center_email_validation_invalid(self):
        """Test validation d'email invalide."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ServiceCenter(
                centerName="Test Center",
                contactEmail="invalid-email"  # Email invalide
            )

        error_messages = str(exc_info.value)
        assert "value is not a valid email address" in error_messages

    def test_service_center_defaults(self):
        """Test des valeurs par défaut."""
        # Act
        center = ServiceCenter(
            centerName="Test Center"
        )

        # Assert
        assert center.location == ""
        assert center.contactEmail is None
        assert center.contactPhone == ""
        assert center.status == ServiceCenterStatus.OPERATIONAL
        assert center.projects == []
        assert center.users == []
        assert center.transversal_activities == []
        assert center.possible_task_statuses == {}
        assert center.possible_task_types == {}
        assert isinstance(center.created_at, datetime)
        assert center.is_deleted is False
        assert center.is_cascade_deleted is False


class TestProjectValidators:
    """Tests pour les validators du modèle Project."""

    def test_project_creation_valid(self, valid_object_id):
        """Test création d'un projet valide."""
        # Act
        project = Project(
            centerId=valid_object_id,
            projectName="Test Project",
            status=ProjectStatus.INPROGRESS,
            transversal_vs_technical_workload_ratio=2.0,
            task_statuses=["TODO", "PROG", "DONE"],
            task_types=["TASK", "BUG"]
        )

        # Assert
        assert project.centerId == valid_object_id
        assert project.projectName == "Test Project"
        assert project.status == ProjectStatus.INPROGRESS
        assert project.transversal_vs_technical_workload_ratio == 2.0
        assert project.task_statuses == ["TODO", "PROG", "DONE"]
        assert project.task_types == ["TASK", "BUG"]

    def test_project_creation_minimal(self):
        """Test création avec données minimales."""
        # Act
        project = Project(
            projectName="Minimal Project",
            status=ProjectStatus.BID
        )

        # Assert
        assert project.projectName == "Minimal Project"
        assert project.status == ProjectStatus.BID
        assert project.centerId is None  # Valeur par défaut
        assert project.transversal_vs_technical_workload_ratio == 1.0  # Valeur par défaut

    def test_project_defaults(self):
        """Test des valeurs par défaut."""
        # Act
        project = Project(
            projectName="Test Project",
            status=ProjectStatus.INPROGRESS
        )

        # Assert
        assert project.roles is None
        assert project.sprints == []
        assert project.centerId is None
        assert project.users == []
        assert isinstance(project.created_at, datetime)
        assert project.is_deleted is False
        assert project.is_cascade_deleted is False
        assert project.transversal_vs_technical_workload_ratio == 1.0
        assert project.project_transversal_activities == []
        assert project.possible_task_statuses == {}
        assert project.possible_task_types == {}
        assert project.task_types == []
        assert project.task_statuses == []


class TestProjectTransversalActivityValidators:
    """Tests pour les validators du modèle ProjectTransversalActivity."""

    def test_project_transversal_activity_creation_valid(self, valid_object_id):
        """Test création d'une activité transversale valide."""
        # Act
        activity = ProjectTransversalActivity(
            project_id=valid_object_id,
            activity="Test Activity",
            meaning="Test activity description",
            default=True
        )

        # Assert
        assert activity.project_id == valid_object_id
        assert activity.activity == "Test Activity"
        assert activity.meaning == "Test activity description"
        assert activity.default is True

    def test_project_transversal_activity_defaults(self, valid_object_id):
        """Test des valeurs par défaut."""
        # Act
        activity = ProjectTransversalActivity(
            project_id=valid_object_id,
            activity="Test Activity"
        )

        # Assert
        assert activity.meaning == ""  # Valeur par défaut
        assert activity.default is True  # Valeur par défaut
        assert isinstance(activity.created_at, datetime)
        assert activity.is_deleted is False
        assert activity.is_cascade_deleted is False


class TestSprintValidators:
    """Tests pour les validators du modèle Sprint."""

    def test_sprint_creation_valid(self, valid_object_id, sample_datetime, sample_future_datetime):
        """Test création d'un sprint valide."""
        # Act
        sprint = Sprint(
            projectId=valid_object_id,
            sprintName="Test Sprint",
            status=SprintStatus.INPROGRESS,
            startDate=sample_datetime,
            dueDate=sample_future_datetime,
            capacity=40.0
        )

        # Assert
        assert sprint.projectId == valid_object_id
        assert sprint.sprintName == "Test Sprint"
        assert sprint.status == SprintStatus.INPROGRESS
        assert sprint.startDate == sample_datetime
        assert sprint.dueDate == sample_future_datetime
        assert sprint.capacity == 40.0

    def test_sprint_defaults(self, valid_object_id, sample_datetime, sample_future_datetime):
        """Test des valeurs par défaut."""
        # Act
        sprint = Sprint(
            projectId=valid_object_id,
            sprintName="Test Sprint",
            startDate=sample_datetime,
            dueDate=sample_future_datetime,
            capacity=40.0
        )

        # Assert
        assert sprint.status == SprintStatus.TODO  # Valeur par défaut
        assert sprint.sprint_transversal_activities == []
        assert sprint.task == []
        assert isinstance(sprint.created_at, datetime)
        assert sprint.is_deleted is False
        assert sprint.is_cascade_deleted is False
        assert sprint.task_statuses == []
        assert sprint.task_types == []


class TestSprintTransversalActivityValidators:
    """Tests pour les validators du modèle SprintTransversalActivity."""

    def test_sprint_transversal_activity_creation_valid(self, valid_object_id):
        """Test création d'une activité transversale de sprint valide."""
        # Act
        activity = SprintTransversalActivity(
            sprintId=valid_object_id,
            activity="Test Sprint Activity",
            meaning="Test sprint activity description",
            time_spent=5.0
        )

        # Assert
        assert activity.sprintId == valid_object_id
        assert activity.activity == "Test Sprint Activity"
        assert activity.meaning == "Test sprint activity description"
        assert activity.time_spent == 5.0

    def test_sprint_transversal_activity_defaults(self, valid_object_id):
        """Test des valeurs par défaut."""
        # Act
        activity = SprintTransversalActivity(
            sprintId=valid_object_id,
            activity="Test Activity"
        )

        # Assert
        assert activity.meaning == ""  # Valeur par défaut
        assert activity.time_spent == 0.0  # Valeur par défaut
        assert isinstance(activity.created_at, datetime)
        assert activity.is_deleted is False
        assert activity.is_cascade_deleted is False


class TestTaskValidators:
    """Tests pour les validators du modèle Task."""

    def test_task_creation_valid(self, valid_object_id, another_object_id):
        """Test création d'une tâche valide."""
        # Act
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task Summary",
            storyPoints=5.0,
            wu="Test WU",
            comment="Test comment",
            deliveryStatus=TaskDeliveryStatus.OK,
            deliveryVersion="v1.0",
            type=TaskType.TASK,
            status=TaskStatus.INPROGRESS,
            rft=TASKRFT.OK,
            technicalLoad=2.5,
            timeSpent=1.0,
            timeRemaining=1.5,
            progress=40.0,
            assignee=[ObjectId()],
            delta=0.0
        )

        # Assert
        assert task.sprintId == valid_object_id
        assert task.projectId == another_object_id
        assert task.key == "TASK-001"
        assert task.summary == "Test Task Summary"
        assert task.storyPoints == 5.0
        assert task.deliveryStatus == TaskDeliveryStatus.OK
        assert task.type == TaskType.TASK
        assert task.status == TaskStatus.INPROGRESS
        assert task.rft == TASKRFT.OK

    def test_task_creation_minimal(self, valid_object_id, another_object_id):
        """Test création avec données minimales."""
        # Act
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-MIN",
            summary="Minimal Task"
        )

        # Assert
        assert task.key == "TASK-MIN"
        assert task.summary == "Minimal Task"
        assert task.storyPoints == 0.0  # Valeur par défaut
        assert task.deliveryStatus == TaskDeliveryStatus.DEFAULT  # Valeur par défaut
        assert task.type == TaskType.TASK  # Valeur par défaut
        assert task.status == TaskStatus.TODO  # Valeur par défaut
        assert task.rft == TASKRFT.DEFAULT  # Valeur par défaut

    def test_task_story_points_validation_positive(self, valid_object_id, another_object_id):
        """Test validation des story points positifs."""
        # Act & Assert - Ne doit pas lever d'exception
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task",
            storyPoints=10.5  # Valeur positive
        )
        assert task.storyPoints == 10.5

    def test_task_story_points_validation_zero(self, valid_object_id, another_object_id):
        """Test validation des story points à zéro."""
        # Act & Assert - Ne doit pas lever d'exception
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task",
            storyPoints=0.0  # Zéro valide
        )
        assert task.storyPoints == 0.0

    def test_task_technical_load_validation_positive(self, valid_object_id, another_object_id):
        """Test validation de la charge technique positive."""
        # Act & Assert - Ne doit pas lever d'exception
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task",
            technicalLoad=5.5  # Valeur positive
        )
        assert task.technicalLoad == 5.5

    def test_task_time_spent_validation_positive(self, valid_object_id, another_object_id):
        """Test validation du temps passé positif."""
        # Act & Assert - Ne doit pas lever d'exception
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task",
            timeSpent=3.25  # Valeur positive
        )
        assert task.timeSpent == 3.25

    def test_task_time_remaining_validation_positive(self, valid_object_id, another_object_id):
        """Test validation du temps restant positif."""
        # Act & Assert - Ne doit pas lever d'exception
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task",
            timeRemaining=2.75  # Valeur positive
        )
        assert task.timeRemaining == 2.75

    def test_task_progress_validation_valid_range(self, valid_object_id, another_object_id):
        """Test validation du progrès dans la plage valide."""
        # Act & Assert - Ne doit pas lever d'exception
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-001",
            summary="Test Task",
            progress=75.5  # Valeur dans la plage valide
        )
        assert task.progress == 75.5

    def test_task_defaults(self, valid_object_id, another_object_id):
        """Test des valeurs par défaut."""
        # Act
        task = Task(
            sprintId=valid_object_id,
            projectId=another_object_id,
            key="TASK-DEFAULT",
            summary="Default Task"
        )

        # Assert
        assert task.storyPoints == 0.0
        assert task.wu == ""
        assert task.comment == ""
        assert task.deliveryStatus == TaskDeliveryStatus.DEFAULT
        assert task.deliveryVersion == ""
        assert task.type == TaskType.TASK
        assert task.status == TaskStatus.TODO
        assert task.rft == TASKRFT.DEFAULT
        assert task.technicalLoad == 0.0
        assert task.timeSpent == 0.0
        assert task.timeRemaining is None
        assert task.progress is None
        assert task.assignee == []
        assert task.delta is None
        assert task.ticketLink is None
        assert task.description is None
        assert isinstance(task.created_at, datetime)
        assert task.is_deleted is False
        assert task.is_cascade_deleted is False


class TestModelCollectionNames:
    """Tests pour vérifier les noms de collection des modèles."""

    def test_user_collection_name(self):
        """Test du nom de collection pour User."""
        assert User.model_config["collection"] == "user"

    def test_director_access_collection_name(self):
        """Test du nom de collection pour DirectorAccess."""
        assert DirectorAccess.model_config["collection"] == "director_access"

    def test_project_access_collection_name(self):
        """Test du nom de collection pour ProjectAccess."""
        assert ProjectAccess.model_config["collection"] == "project_access"

    def test_service_center_collection_name(self):
        """Test du nom de collection pour ServiceCenter."""
        assert ServiceCenter.model_config["collection"] == "service_center"

    def test_project_collection_name(self):
        """Test du nom de collection pour Project."""
        assert Project.model_config["collection"] == "project"

    def test_project_transversal_activity_collection_name(self):
        """Test du nom de collection pour ProjectTransversalActivity."""
        assert ProjectTransversalActivity.model_config["collection"] == "project_transversal_activity"

    def test_sprint_collection_name(self):
        """Test du nom de collection pour Sprint."""
        assert Sprint.model_config["collection"] == "sprint"

    def test_sprint_transversal_activity_collection_name(self):
        """Test du nom de collection pour SprintTransversalActivity."""
        assert SprintTransversalActivity.model_config["collection"] == "sprint_transversal_activity"

    def test_task_collection_name(self):
        """Test du nom de collection pour Task."""
        assert Task.model_config["collection"] == "task"