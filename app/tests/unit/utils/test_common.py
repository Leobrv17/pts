from datetime import datetime

from bson import ObjectId

from app.utils.common import convert_objectid_to_str, validate_objectid, create_pagination_metadata, serialize_datetime


def test_convert_objectid_to_str():
    oids = {
        "1": ObjectId('000000000000000000000001'),
        "2": [
            ObjectId('000000000000000000000002'),
            48,
            "Bonjour"
        ],
        "3": {
            "11": ObjectId('000000000000000000000003'),
            "12": "string"
        }
    }

    expected_result = {
        "1": '000000000000000000000001',
        "2": [
            '000000000000000000000002',
            48,
            "Bonjour"
        ],
        "3": {
            "11": '000000000000000000000003',
            "12": "string"
        }
    }

    assert expected_result == convert_objectid_to_str(oids)


def test_validate_objectid():
    oid = str(ObjectId())
    not_oid = "bweh"

    assert validate_objectid(oid)
    assert not validate_objectid(not_oid)


def test_create_pagination_metadata():
    expected_with_correct_total = {
        "total": 10,
        "page": 1,
        "size": 5,
        "pages": 2,
        "has_next": True,
        "has_prev": False
    }
    assert expected_with_correct_total == create_pagination_metadata(
        total=expected_with_correct_total["total"],
        page=expected_with_correct_total["page"],
        size=expected_with_correct_total["size"]
    )

    expected_with_incorrect_total = {
        "total": -1,
        "page": 2,
        "size": 5,
        "pages": 0,
        "has_next": False,
        "has_prev": True
    }
    assert expected_with_incorrect_total == create_pagination_metadata(
        total=expected_with_incorrect_total["total"],
        page=expected_with_incorrect_total["page"],
        size=expected_with_incorrect_total["size"]
    )


def test_serialize_datetime():
    assert serialize_datetime(None) is None

    dt = datetime(year=2025, month=8, day=12)
    assert serialize_datetime(dt) == "2025-08-12T00:00:00"
