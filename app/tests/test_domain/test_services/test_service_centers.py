from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.schemas.service_center import ServiceCenterBase
from app.models.service_center import ServiceCenterStatus, ServiceCenter
from app.services.service_center_service import ServiceCenterService
from schemas.service_center import ServiceCenterUpdate


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.save = AsyncMock()
    engine.find_one = AsyncMock()
    engine.find = AsyncMock()
    engine.insert_one = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_create_center(mock_engine):
    """Test POST api/service_centers/ service-side"""
    center_data = ServiceCenterBase(
        centerName="Test center",
        location="Toulouse",
        contactEmail="email@sii.fr",
        contactPhone="0132456789",
        status=ServiceCenterStatus.OPERATIONAL
    )

    mock_engine.save.return_value = None
    center_service = ServiceCenterService(mock_engine)
    response_center = await center_service.create_service_center(center_data)

    expected_result = ServiceCenter(
        id=response_center.id,
        centerName=center_data.centerName,
        location=center_data.location,
        contactEmail=center_data.contactEmail,
        contactPhone=center_data.contactPhone,
        status=center_data.status,
        projects=[],
        users=[],
        created_at=response_center.created_at,
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={}
    )

    assert response_center == expected_result


@pytest.mark.asyncio
async def test_get_center_by_id_not_found(mock_engine):
    """Test get_center_by_id with center not found"""
    mock_engine.find_one.return_value = None
    center_service = ServiceCenterService(mock_engine)
    with pytest.raises(HTTPException):
        await center_service.get_service_center_by_id(str(ObjectId()))


@pytest.mark.asyncio
async def test_get_centers(mock_engine):
    """Test GET api/service_centers/ service-side"""
    center1 = ServiceCenter(
        id=ObjectId(),
        centerName="Center1",
        location="Location1",
        contactEmail="email1@sii.com",
        contactPhone="1111111111",
        status=ServiceCenterStatus.OPERATIONAL,
        projects=[],
        users=[],
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={}
    )
    center2 = ServiceCenter(
        id=ObjectId(),
        centerName="Center2",
        location="Location2",
        contactEmail="email2@sii.com",
        contactPhone="22222222222",
        status=ServiceCenterStatus.CLOSED,
        projects=[],
        users=[],
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={}
    )

    centers_found = [c for c in [center1, center2]
                     if c.status == ServiceCenterStatus.OPERATIONAL]
    mock_engine.find.return_value = centers_found
    center_service = ServiceCenterService(mock_engine)
    response, _ = await center_service.get_service_centers(status="Operational")

    assert response == [center1]


@pytest.mark.asyncio
async def test_update_center(mock_engine):
    """Test PUT api/service_centers/ service-side"""
    center = ServiceCenter(
        id=ObjectId(),
        centerName="Center1",
        location="Location1",
        contactEmail="email1@sii.com",
        contactPhone="1111111111",
        status=ServiceCenterStatus.OPERATIONAL,
        projects=[],
        users=[],
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={}
    )
    center_update = ServiceCenterUpdate(
        id=str(center.id),
        centerName="New name",
        location="New location",
        status="Closed"
    )

    mock_engine.find_one.return_value = center
    center_service = ServiceCenterService(mock_engine)
    updated_center = await center_service.update_service_center(center_update)

    expected_result = ServiceCenter(
        id=center.id,
        centerName=center_update.centerName,
        location=center_update.location,
        contactEmail=center.contactEmail,
        contactPhone=center.contactPhone,
        status=ServiceCenterStatus.CLOSED,
        created_at=center.created_at,
        projects=[],
        users=[],
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={}
    )

    assert expected_result == updated_center


@pytest.mark.asyncio
async def test_delete_center(mock_engine):
    """Test DELETE api/service_centers/ service-side"""
    center = ServiceCenter(
        id=ObjectId(),
        centerName="Center1",
        location="Location1",
        contactEmail="email1@sii.com",
        contactPhone="1111111111",
        status=ServiceCenterStatus.OPERATIONAL,
        projects=[],
        users=[],
        transversal_activities=[],
        possible_task_statuses={},
        possible_task_types={},
        is_deleted=False
    )

    mock_engine.save.return_value = center
    mock_engine.find_one.return_value = center
    center_service = ServiceCenterService(mock_engine)
    assert await center_service.delete_service_center(str(center.id))
    assert center.is_deleted
