"""Tests for admin agent."""

import json
import pytest
from src.dynamic_db import init_db, save_reservation, get_reservation, update_reservation_status


SAMPLE_DATA = {
    "static": [{"id": "test", "text": "Test."}],
    "dynamic": {
        "working_hours": {"monday_friday": "06:00-23:00"},
        "pricing": {"hourly": 5.0, "currency": "USD"},
        "availability": [{"level": "L1", "available": 10, "total": 50}]
    }
}


@pytest.fixture
def db(tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(SAMPLE_DATA))
    db_file = str(tmp_path / "test.db")
    init_db(db_path=db_file, data_path=str(data_file))
    return db_file


def _make_reservation(db):
    return save_reservation({
        "first_name": "John", "last_name": "Doe",
        "license_plate": "ABC-123",
        "start_time": "2025-07-01 09:00", "end_time": "2025-07-01 17:00"
    }, db_path=db)


def test_approve_reservation(db):
    rid = _make_reservation(db)
    updated = update_reservation_status(rid, "approved", "Looks good", db)
    assert updated["status"] == "approved"
    assert updated["admin_comment"] == "Looks good"


def test_reject_reservation(db):
    rid = _make_reservation(db)
    updated = update_reservation_status(rid, "rejected", "No spaces", db)
    assert updated["status"] == "rejected"
    assert updated["admin_comment"] == "No spaces"


def test_invalid_status_rejected(db):
    rid = _make_reservation(db)
    result = update_reservation_status(rid, "invalid_status", "", db)
    assert result is None


def test_reservation_stays_pending_until_reviewed(db):
    rid = _make_reservation(db)
    res = get_reservation(rid, db)
    assert res["status"] == "pending_approval"