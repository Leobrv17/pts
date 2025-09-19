"""Fixtures de données pour les projets."""

from bson import ObjectId
from datetime import datetime, timezone

from app.models.project import Project, ProjectStatus, ProjectTransversalActivity
from app.schemas.project import ProjectBase, ProjectCreate, ProjectUpdate


# ===== DONNÉES DE TEST POUR LES PROJETS =====

def get_sample_project_data():
    """Données de base pour créer un projet de test."""
    return {
        "centerId": str(ObjectId()),
        "projectName": "Sample Test Project",
        "status": ProjectStatus.INPROGRESS,
        "technicalLoadRatio": 2.0,
        "taskStatuses": ["TODO", "PROG", "REV", "DONE"],
        "taskTypes": ["TASK", "BUG", "STORY"]
    }


def get_project_base_schema():
    """Schema ProjectBase pour les tests."""
    data = get_sample_project_data()
    return ProjectBase(**data)


def get_project_create_schema():
    """Schema ProjectCreate pour les tests."""
    data = get_sample_project_data()
    return ProjectCreate(
        centerId=data["centerId"],
        projectName=data["projectName"],
        status=data["status"].value,
        sprints=None
    )


def get_project_update_schema(project_id: str):
    """Schema ProjectUpdate pour les tests."""
    return ProjectUpdate(
        id=project_id,
        projectName="Updated Project Name",
        status=ProjectStatus.DONE,
        technicalLoadRatio=3.0,
        taskStatuses=["TODO", "DONE"],
        taskTypes=["TASK"]
    )


def get_multiple_projects_data():
    """Données pour plusieurs projets de test."""
    center_id = ObjectId()
    return [
        {
            "id": ObjectId(),
            "centerId": center_id,
            "projectName": "Project Alpha",
            "status": ProjectStatus.INPROGRESS,
            "sprints": [],
            "users": [],
            "transversal_vs_technical_workload_ratio": 2.0,
            "project_transversal_activities": [],
            "task_statuses": ["TODO", "PROG", "DONE"],
            "task_types": ["TASK", "BUG"]
        },
        {
            "id": ObjectId(),
            "centerId": center_id,
            "projectName": "Project Beta",
            "status": ProjectStatus.DONE,
            "sprints": [],
            "users": [],
            "transversal_vs_technical_workload_ratio": 1.5,
            "project_transversal_activities": [],
            "task_statuses": ["TODO", "DONE"],
            "task_types": ["TASK"]
        },
        {
            "id": ObjectId(),
            "centerId": ObjectId(),  # Différent centre
            "projectName": "Project Gamma",
            "status": ProjectStatus.BID,
            "sprints": [],
            "users": [],
            "transversal_vs_technical_workload_ratio": 1.0,
            "project_transversal_activities": [],
            "task_statuses": ["TODO"],
            "task_types": ["TASK"]
        }
    ]


def create_project_models(projects_data):
    """Crée des instances de Project à partir des données."""
    return [Project(**data) for data in projects_data]


# ===== DONNÉES POUR LES ACTIVITÉS TRANSVERSALES =====

def get_default_transversal_activities():
    """Activités transversales par défaut d'un projet."""
    return [
        {"activity": "Ceremonies", "meaning": "SCRUM Meetings"},
        {"activity": "Project meetings", "meaning": "Other Meetings"},
        {"activity": "Estimations", "meaning": "Analysis, Questions/answers, Cost of production"},
        {"activity": "Deliveries", "meaning": "Preparation and test before sprint delivery and/or deployment"},
        {"activity": "Maintenance", "meaning": "Environment maintenance, configuration management"},
        {"activity": "Team management", "meaning": "Team organisation and project management / TL"},
        {"activity": "Capitalisation", "meaning": "Global project capitalisation"},
        {"activity": "Internal trainings", "meaning": "Team skills ramp-up"},
        {"activity": "Agency meetings", "meaning": "Meeting with HR, Business, medical appointment"},
        {"activity": "Lost Time", "meaning": "Example: dysfunctional accesses"}
    ]


def get_project_transversal_activity_data(project_id: ObjectId):
    """Données pour une activité transversale de projet."""
    return {
        "id": ObjectId(),
        "project_id": project_id,
        "activity": "Test Activity",
        "meaning": "Test activity description",
        "default": True,
        "created_at": datetime.now(timezone.utc),
        "is_deleted": False,
        "is_cascade_deleted": False
    }


def create_project_transversal_activity_model(project_id: ObjectId):
    """Crée une instance de ProjectTransversalActivity."""
    data = get_project_transversal_activity_data(project_id)
    return ProjectTransversalActivity(**data)


def get_multiple_transversal_activities_data(project_id: ObjectId):
    """Données pour plusieurs activités transversales."""
    return [
        {
            "id": ObjectId(),
            "project_id": project_id,
            "activity": "Ceremonies",
            "meaning": "Daily standups, sprint planning, retrospectives",
            "default": True,
            "created_at": datetime.now(timezone.utc),
            "is_deleted": False,
            "is_cascade_deleted": False
        },
        {
            "id": ObjectId(),
            "project_id": project_id,
            "activity": "Documentation",
            "meaning": "Technical documentation, user guides",
            "default": False,
            "created_at": datetime.now(timezone.utc),
            "is_deleted": False,
            "is_cascade_deleted": False
        }
    ]


# ===== DONNÉES D'ERREUR POUR LES TESTS NÉGATIFS =====

def get_invalid_project_data():
    """Données invalides pour tester les erreurs."""
    return {
        "invalid_object_ids": [
            "invalid_id",
            "123",
            "",
            "not_an_objectid"
        ],
        "invalid_status_values": [
            "INVALID_STATUS",
            "NotAStatus",
            123,
            None
        ],
        "invalid_ratios": [
            -1.0,
            0.0,
            "not_a_number",
            None
        ]
    }


# ===== BUILDERS POUR LES TESTS =====

class ProjectDataBuilder:
    """Builder pour créer des données de projet personnalisées."""

    def __init__(self):
        self.data = get_sample_project_data()

    def with_center_id(self, center_id: str):
        self.data["centerId"] = center_id
        return self

    def with_name(self, name: str):
        self.data["projectName"] = name
        return self

    def with_status(self, status: ProjectStatus):
        self.data["status"] = status
        return self

    def with_ratio(self, ratio: float):
        self.data["technicalLoadRatio"] = ratio
        return self

    def with_task_statuses(self, statuses: list):
        self.data["taskStatuses"] = statuses
        return self

    def with_task_types(self, types: list):
        self.data["taskTypes"] = types
        return self

    def build_base_schema(self):
        return ProjectBase(**self.data)

    def build_create_schema(self):
        return ProjectCreate(
            centerId=self.data["centerId"],
            projectName=self.data["projectName"],
            status=self.data["status"].value
        )

    def build_model(self):
        model_data = self.data.copy()
        model_data["centerId"] = ObjectId(model_data["centerId"])
        model_data["id"] = ObjectId()
        model_data["sprints"] = []
        model_data["users"] = []
        model_data["transversal_vs_technical_workload_ratio"] = model_data.pop("technicalLoadRatio")
        model_data["project_transversal_activities"] = []
        model_data["task_statuses"] = model_data.pop("taskStatuses")
        model_data["task_types"] = model_data.pop("taskTypes")
        return Project(**model_data)