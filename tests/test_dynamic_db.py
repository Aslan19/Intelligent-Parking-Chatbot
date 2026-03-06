from src.dynamic_db import (
    get_dynamic_context, save_reservation, get_reservation,
    get_pending_reservations, update_reservation_status
)
from tests.conftest import SAMPLE_RESERVATION


def test_context_has_hours(db):
    ctx = get_dynamic_context(db)
    assert "06:00 - 23:00" in ctx


def test_context_has_pricing(db):
    ctx = get_dynamic_context(db)
    assert "5.0" in ctx


def test_context_has_availability(db):
    ctx = get_dynamic_context(db)
    assert "L1" in ctx


def test_save_and_get_reservation(db):
    rid = save_reservation(SAMPLE_RESERVATION, db)
    r = get_reservation(rid, db)
    assert r["first_name"] == "John"
    assert r["status"] == "pending_approval"


def test_pending_list(db):
    save_reservation(SAMPLE_RESERVATION, db)
    pending = get_pending_reservations(db)
    assert len(pending) == 1


def test_approve(db):
    rid = save_reservation(SAMPLE_RESERVATION, db)
    updated = update_reservation_status(rid, "approved", "OK", db)
    assert updated["status"] == "approved"
    assert updated["admin_comment"] == "OK"


def test_reject(db):
    rid = save_reservation(SAMPLE_RESERVATION, db)
    updated = update_reservation_status(rid, "rejected", "Full", db)
    assert updated["status"] == "rejected"


def test_invalid_status(db):
    rid = save_reservation(SAMPLE_RESERVATION, db)
    result = update_reservation_status(rid, "invalid", "", db)
    assert result is None