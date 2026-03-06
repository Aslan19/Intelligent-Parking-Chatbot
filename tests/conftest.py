"""Shared test fixtures."""

import json
import pytest

SAMPLE_DATA = {
    "static": [
        {"id": "general", "text": "CityCenter parking at 123 Main Street Metropolis."},
        {"id": "policies", "text": "Max height 2.1m. Lost ticket fee $25."}
    ],
    "dynamic": {
        "working_hours": {"monday_friday": "06:00 - 23:00", "saturday": "07:00 - 22:00"},
        "pricing": {"hourly": 5.0, "daily_max": 30.0, "currency": "USD"},
        "availability": [{"level": "L1", "available": 10, "total": 50}]
    }
}

SAMPLE_RESERVATION = {
    "first_name": "John",
    "last_name": "Doe",
    "license_plate": "ABC-123",
    "start_time": "2025-07-01 09:00",
    "end_time": "2025-07-01 17:00",
}


@pytest.fixture
def data_file(tmp_path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps(SAMPLE_DATA))
    return str(f)


@pytest.fixture
def db(tmp_path, data_file):
    from src.dynamic_db import init_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path=db_path, data_path=data_file)
    return db_path


@pytest.fixture
def output_file(tmp_path):
    return str(tmp_path / "confirmed.txt")