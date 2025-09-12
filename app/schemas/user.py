"""User schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from app.models.user import UserTypeEnum, AccessLevelEnum


class DirectorAccessBase(BaseModel):
    """Base schema for director access."""
    id: Optional[str] = Field(default=None, description="Director access ID")
    serviceCenterId: str = Field(..., description="Service center ID")


class DirectorAccessResponse(BaseModel):
    """Schema for director access response."""
    id: str = Field(..., description="Director access ID")
    serviceCenterId: str = Field(..., description="Service center ID")
    serviceCenterName: str = Field(..., description="Service center name")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectAccessBase(BaseModel):
    """Base schema for project access."""
    id: Optional[str] = Field(default=None, description="Project access ID")
    serviceCenterId: str = Field(..., description="Service center ID")
    projectId: str = Field(..., description="Project ID")
    accessLevel: AccessLevelEnum = Field(..., description="Access level")
    occupancyRate: float = Field(..., ge=0.0, le=100.0, description="Occupancy rate percentage")


class ProjectAccessResponse(BaseModel):
    """Schema for project access response."""
    id: str = Field(..., description="Project access ID")
    serviceCenterId: str = Field(..., description="Service center ID")
    serviceCenterName: str = Field(..., description="Service center name")
    projectId: str = Field(..., description="Project ID")
    projectName: str = Field(..., description="Project name")
    accessLevel: AccessLevelEnum = Field(..., description="Access level")
    occupancyRate: float = Field(..., ge=0.0, le=100.0, description="Occupancy rate percentage")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserBase(BaseModel):
    """Base user schema."""
    id: Optional[str] = Field(default=None, description="User ID")
    firstName: str = Field(..., min_length=1, max_length=100, description="First name")
    familyName: str = Field(..., min_length=1, max_length=100, description="Family name")
    email: EmailStr = Field(..., description="Email address")
    type: UserTypeEnum = Field(default=UserTypeEnum.NORMAL, description="User type")
    registrationNumber: Optional[str] = Field(default="", max_length=50, description="Registration number/matricule")
    trigram: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$", description="3-letter trigram")


class UserLite(BaseModel):
    """Schema for user lite with access management."""
    id: Optional[str] = Field(default=None, description="User ID")
    firstName: str = Field(..., min_length=1, max_length=100, description="First name")
    familyName: str = Field(..., min_length=1, max_length=100, description="Family name")
    email: EmailStr = Field(..., description="Email address")
    type: UserTypeEnum = Field(default=UserTypeEnum.NORMAL, description="User type")
    directorAccessList: Optional[List[DirectorAccessBase]] = Field(default_factory=list, description="Director access list")
    projectAccessList: Optional[List[ProjectAccessBase]] = Field(default_factory=list, description="Project access list")
    registrationNumber: Optional[str] = Field(default="", max_length=50, description="Registration number/matricule")
    trigram: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$", description="3-letter trigram")


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class DirectorAccessCreate(DirectorAccessBase):
    """Schema for creating director access."""
    userId: str = Field(..., description="User ID")


class DirectorAccessUpdate(BaseModel):
    """Schema for updating director access."""
    id: str = Field(..., description="Director access ID")
    serviceCenterName: Optional[str] = None


class ProjectAccessCreate(ProjectAccessBase):
    """Schema for creating project access."""
    userId: str = Field(..., description="User ID")


class ProjectAccessUpdate(BaseModel):
    """Schema for updating project access."""
    id: str = Field(..., description="Project access ID")
    serviceCenterName: Optional[str] = None
    projectName: Optional[str] = None
    accessLevel: Optional[AccessLevelEnum] = None
    occupancyRate: Optional[float] = Field(None, ge=0.0, le=100.0)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    firstName: Optional[str] = Field(None, min_length=1, max_length=100)
    familyName: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    type: Optional[UserTypeEnum] = None
    registrationNumber: Optional[str] = Field(None, max_length=50)
    trigram: Optional[str] = Field(None, min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    # Nouveaux champs pour gérer les accès
    directorAccesses: Optional[List[DirectorAccessCreate]] = Field(None, description="Director accesses to add/update")
    projectAccesses: Optional[List[ProjectAccessCreate]] = Field(None, description="Project accesses to add/update")
    removeDirectorAccesses: Optional[List[str]] = Field(None, description="Director access IDs to remove")
    removeProjectAccesses: Optional[List[str]] = Field(None, description="Project access IDs to remove")


class UserResponse(UserBase):
    """Schema for user response."""
    id: str = Field(..., description="User ID")
    directorAccessList: List[DirectorAccessResponse] = Field(default_factory=list, description="Director access list")
    projectAccessList: List[ProjectAccessResponse] = Field(default_factory=list, description="Project access list")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserListResponse(BaseModel):
    """Schema for user list response."""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserByNameRequest(BaseModel):
    """Schema for user search by name request."""
    name: Optional[str] = Field(None, description="Name fragment to search for")
    isDeleted: Optional[bool] = Field(default=False, description="Include deleted users")


class UserByNameResponse(BaseModel):
    """Schema for user search by name response."""
    users: List[UserResponse]

class UserProjectSummary(BaseModel):
    """Schema pour résumer un projet d'un utilisateur."""
    id: str = Field(..., description="Project ID")
    projectName: str = Field(..., description="Project name")
    accessLevel: AccessLevelEnum = Field(..., description="Access level")
    occupancyRate: float = Field(..., ge=0.0, le=100.0, description="Occupancy rate percentage")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserServiceCenterResponse(BaseModel):
    """Schema pour un utilisateur dans le contexte d'un service center."""
    id: str = Field(..., description="User ID")
    firstName: str = Field(..., description="First name")
    familyName: str = Field(..., description="Family name")
    projects: List[UserProjectSummary] = Field(default_factory=list, description="List of projects in this service center")
    totalOccupancyRate: float = Field(default=0.0, ge=0.0, description="Sum of occupancy rates across all projects")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }