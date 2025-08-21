"""Common utility functions."""

from typing import Any, Dict, Optional
from bson import ObjectId
from datetime import datetime


def convert_objectid_to_str(data: Any) -> Any:
    """Convert ObjectId fields to strings recursively."""
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        return data


def validate_objectid(object_id: str) -> bool:
    """Validate if string is a valid ObjectId."""
    try:
        ObjectId(object_id)
        return True
    except Exception as e:
        print(str(e))
        return False


def create_pagination_metadata(
        total: int,
        page: int,
        size: int
) -> Dict[str, Any]:
    """Create pagination metadata."""
    from math import ceil

    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if total > 0 else 0,
        "has_next": page * size < total,
        "has_prev": page > 1
    }


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to ISO format string."""
    return dt.isoformat() if dt else None
