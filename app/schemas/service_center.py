"""Service center schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from app.models.service_center import ServiceCenterStatus
from app.schemas.project import ProjectLightResponse
from app.schemas.user import UserResponse


class ServiceCenterBase(BaseModel):
    """Base service center schema."""
    centerName: str = Field(..., min_length=1, max_length=200, description="Service center name")
    location: Optional[str] = Field(default="", description="Service center location")
    contactEmail: Optional[EmailStr] = Field(default="default@email.com", description="Contact email")
    contactPhone: Optional[str] = Field(default="", description="Contact phone")
    status: Optional[ServiceCenterStatus] = Field(default=ServiceCenterStatus.OPERATIONAL, description="Service center status")


class ServiceCenterUpdate(BaseModel):
    """Schema for updating a service center."""
    id: str = Field(..., description="Center ID")
    centerName: Optional[str] = Field(None, min_length=1, max_length=200, description="Service Center name")
    location: Optional[str] = Field(None, description="Physical location of service center")
    contactEmail: Optional[EmailStr] = Field(None, description="contact email of service center")
    contactPhone: Optional[str] = Field(None, description="contact phone of service center")
    status: Optional[ServiceCenterStatus] = Field(None, description="Service center status (Operational/Closed)")


class ServiceCenterResponse(ServiceCenterBase):
    """Schema for service center response."""
    id: str = Field(..., description="Center ID")
    projects: List[ProjectLightResponse] = Field(default_factory=list, description="The projects included in the center, in light version.")
    users: List[UserResponse] = Field(default_factory=list, description="The users that work in the center.")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ServiceCenterListResponse(BaseModel):
    """Schema for service center list response."""
    service_centers: List[ServiceCenterResponse]
    total: int
    page: int
    size: int
    pages: int

class ServiceCenterLightResponse(BaseModel):
    """Light schema for service center with only basic information."""
    id: str = Field(alias="_id", description="Service center ID")
    centerName: str = Field(..., description="Service center name")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }


class ServiceCenterListResponseLight(BaseModel):
    """Light schema for service center list response."""
    serviceCenters: List[ServiceCenterLightResponse]
    total: int
    page: int
    size: int
    pages: int
