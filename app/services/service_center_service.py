"""Service center service layer."""

from typing import List, Optional
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from app.models.service_center import ServiceCenter
from app.schemas.service_center import ServiceCenterUpdate, ServiceCenterBase


class ServiceCenterService:
    """Service class for service center operations."""

    # Map schema fields to model fields
    _field_mapping = {
        'centerName': 'centerName',
        'contactEmail': 'contactEmail',
        'contactPhone': 'contactPhone',
        'location': 'location',
        'status': 'status'
    }

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def create_service_center(self, service_center_data: ServiceCenterBase) -> ServiceCenter:
        """Create a new service center."""
        service_center = ServiceCenter(
            centerName=service_center_data.centerName,
            location=service_center_data.location,
            contactEmail=service_center_data.contactEmail,
            contactPhone=service_center_data.contactPhone,
            status=service_center_data.status,
            projects=[],
            users=[],
            transversal_activities=[],
            possible_task_statuses={},
            possible_task_types={},
        )

        try:
            await self.engine.save(service_center)
            return service_center
        except Exception as e: # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating service center: {str(e)}"
            )

    async def get_service_center_by_id(self, service_center_id: str, is_deleted: bool = False) -> Optional[ServiceCenter]:
        """Get service center by ID."""
        try:
            object_id = ObjectId(service_center_id)
            center = await self.engine.find_one(
                ServiceCenter,
                (ServiceCenter.id == object_id) & (ServiceCenter.is_deleted == is_deleted)
            )
        except Exception as e: # pragma: no cover
            print(str(e))
            return None

        if not center:
            raise HTTPException(
                status_code=404,
                detail=f"Service center {service_center_id} not found."
            )
        return center

    async def get_service_centers(
            self,
            skip: int = 0,
            limit: int = 100,
            status: Optional[str] = None,
            is_deleted: bool = False
    ) -> tuple[List[ServiceCenter], int]:
        """Get service centers in light format (only id and name)."""
        query_filter = ServiceCenter.is_deleted == is_deleted

        if status:
            query_filter = query_filter & (ServiceCenter.status == status)

        # Utiliser une projection pour récupérer seulement les champs nécessaires
        service_centers = await self.engine.find(
            ServiceCenter,
            query_filter,
            skip=skip,
            limit=limit
        )
        total = await self.engine.count(ServiceCenter, query_filter)

        return service_centers, total

    async def update_service_center(
            self, service_center_update: ServiceCenterUpdate
    ) -> Optional[ServiceCenter]:
        """Update service center."""
        service_center = await self.get_service_center_by_id(service_center_update.id)
        update_data = service_center_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field != 'id':
                setattr(service_center, self._field_mapping[field], value)

        try:
            await self.engine.save(service_center)
            return service_center
        except Exception as e: # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating service center: {str(e)}"
            )

    async def delete_service_center(self, service_center_id: str) -> bool:
        """Soft delete service center."""
        service_center = await self.get_service_center_by_id(service_center_id)

        service_center.is_deleted = True
        await self.engine.save(service_center)
        return True