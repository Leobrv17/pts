"""User schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from app.models.user import UserTypeEnum, AccessLevelEnum


class DirectorAccessBase(BaseModel):
    """Base schema for director access."""
    service_center_id: str = Field(..., description="Service center ID")
    service_center_name: str = Field(..., description="Service center name")


class DirectorAccessResponse(DirectorAccessBase):
    """Schema for director access response."""
    id: str = Field(..., description="Director access ID")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectAccessBase(BaseModel):
    """Base schema for project access."""
    service_center_id: str = Field(..., description="Service center ID")
    service_center_name: str = Field(..., description="Service center name")
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    access_level: AccessLevelEnum = Field(..., description="Access level")
    occupancy_rate: float = Field(..., ge=0.0, le=100.0, description="Occupancy rate percentage")


class ProjectAccessResponse(ProjectAccessBase):
    """Schema for project access response."""
    id: str = Field(..., description="Project access ID")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserBase(BaseModel):
    """Base user schema."""
    firstName: str = Field(..., min_length=1, max_length=100, description="First name")
    family_name: str = Field(..., min_length=1, max_length=100, description="Family name")
    email: EmailStr = Field(..., description="Email address")
    type: UserTypeEnum = Field(default=UserTypeEnum.NORMAL, description="User type")
    registration_number: Optional[str] = Field(default="", max_length=50, description="Registration number/matricule")
    trigram: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$", description="3-letter trigram")


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class DirectorAccessCreate(DirectorAccessBase):
    """Schema for creating director access."""
    user_id: str = Field(..., description="User ID")


class DirectorAccessUpdate(BaseModel):
    """Schema for updating director access."""
    id: str = Field(..., description="Director access ID")
    service_center_name: Optional[str] = None


class ProjectAccessCreate(ProjectAccessBase):
    """Schema for creating project access."""
    user_id: str = Field(..., description="User ID")


class ProjectAccessUpdate(BaseModel):
    """Schema for updating project access."""
    id: str = Field(..., description="Project access ID")
    service_center_name: Optional[str] = None
    project_name: Optional[str] = None
    access_level: Optional[AccessLevelEnum] = None
    occupancy_rate: Optional[float] = Field(None, ge=0.0, le=100.0)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    family_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    type: Optional[UserTypeEnum] = None
    registration_number: Optional[str] = Field(None, max_length=50)
    trigram: Optional[str] = Field(None, min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    # Nouveaux champs pour gérer les accès
    director_accesses: Optional[List[DirectorAccessCreate]] = Field(None, description="Director accesses to add/update")
    project_accesses: Optional[List[ProjectAccessCreate]] = Field(None, description="Project accesses to add/update")
    remove_director_accesses: Optional[List[str]] = Field(None, description="Director access IDs to remove")
    remove_project_accesses: Optional[List[str]] = Field(None, description="Project access IDs to remove")


class UserResponse(UserBase):
    """Schema for user response."""
    id: str = Field(alias="_id", description="User ID")
    director_access_list: List[DirectorAccessResponse] = Field(default_factory=list, description="Director access list")
    project_access_list: List[ProjectAccessResponse] = Field(default_factory=list, description="Project access list")

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
    is_deleted: Optional[bool] = Field(default=False, description="Include deleted users")


class UserByNameResponse(BaseModel):
    """Schema for user search by name response."""
    users: List[UserResponse]