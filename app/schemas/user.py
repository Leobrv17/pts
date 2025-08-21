"""User schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from app.models.user import UserRole, UserStatus
from app.schemas.role import DirectorAccess


class UserTypeEnum(str, Enum):
    NORMAL = "Normal",
    SUPPORT = "Support",
    ADMIN = "Admin"


class UserBase(BaseModel):
    """Base user schema."""
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = Field(..., description="User email.")
    type: UserTypeEnum = Field(..., description="The supertype of user: Normal, Support, Admin.")
    DirectorAccessList: Optional[DirectorAccess] = Field(..., description="")
    status: UserStatus = UserStatus.ACTIVE
    trigram: str = Field(default="", pattern="[A-Z]{3}")
    registration: Optional[str] = Field(..., description="User registration number")


class UserCreate(UserBase):
    """Schema for creating a user."""
    projects: Optional[List[str]] = Field(default_factory=list)
    centers: Optional[List[str]] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    firstName: Optional[str] = Field(None, min_length=1, max_length=100)
    lastName: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    trigram: Optional[str] = Field(None, max_length=3)
    projects: Optional[List[str]] = None
    project_percentages: Optional[Dict[str, float]] = None
    project_anonymity: Optional[Dict[str, bool]] = None
    centers: Optional[List[str]] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: str = Field(alias="_id")

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