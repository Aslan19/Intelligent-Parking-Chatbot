"""Tests for the dynamic SQLite database."""

import json
import os
import tempfile
import pytest
from src.dynamic_db import init_db, get_dynamic_context, save_reservation

SAMPLE_DATA = {
    "static": [{"id": "test", "text": "Test parking."}],
    "dynamic": {
        "working_hours": {"monday_friday": "06:00 - 23:00", "saturday": "07:00 - 22:00"},
        "pricing": {"hourly": 5.0, "daily_max": 30.0, "currency": "USD"},
        "availability": [{"level": "L1", "available": 10, "total": 50}]
    }
}


@pytest.fixture
def db_and_data(tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(SAMPLE_DATA))
    db_file = str(tmp_path / "test.db")
    init_db(db_path=db_file, data_path=str(data_file))
    return db_file


def test_dynamic_context_contains_hours(db_and_data):
    ctx = get_dynamic_context(db_and_data)
    assert "06:00 - 23:00" in ctx
    assert "saturday" in ctx.lower()


def test_dynamic_context_contains_pricing(db_and_data):
    ctx = get_dynamic_context(db_and_data)
    assert "5.0" in ctx
    assert "hourly" in ctx


def test_dynamic_context_contains_availability(db_and_data):
    ctx = get_dynamic_context(db_and_data)
    assert "L1" in ctx
    assert "10" in ctx


def test_save_reservation(db_and_data):
    rid = save_reservation({
        "first_name": "Jane",
        "last_name": "Doe",
        "license_plate": "ABC-123",
        "start_time": "2025-07-01 09:00",
        "end_time": "2025-07-01 17:00"
    }, db_path=db_and_data)
    assert isinstance(rid, int)
    assert rid >= 1