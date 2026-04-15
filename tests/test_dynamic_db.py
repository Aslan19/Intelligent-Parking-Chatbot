from src.dynamic_db import (
    get_dynamic_context, save_reservation, get_reservation,
    get_pending_reservations, update_reservation_status
)
from src.models import Reservation, ReservationCreate            # ✅ CHANGE #6

SAMPLE = ReservationCreate(                                      # ✅ CHANGE #6
    first_name="John", last_name="Doe", license_plate="ABC-123",
    start_time="2025-07-01 09:00", end_time="2025-07-01 17:00"
)


def test_context_has_hours(db):
    assert "06:00 - 23:00" in get_dynamic_context(db)


def test_context_has_pricing(db):
    assert "5.0" in get_dynamic_context(db)


def test_context_has_availability(db):
    assert "L1" in get_dynamic_context(db)


def test_save_returns_model(db):
    saved = save_reservation(SAMPLE, db)
    assert isinstance(saved, Reservation)                        # ✅ CHANGE #6: returns model
    assert saved.first_name == "John"
    assert saved.status == "pending_approval"


def test_get_returns_model(db):
    saved = save_reservation(SAMPLE, db)
    r = get_reservation(saved.id, db)
    assert isinstance(r, Reservation)                            # ✅ CHANGE #6
    assert r.license_plate == "ABC-123"


def test_pending_returns_model_list(db):
    save_reservation(SAMPLE, db)
    pending = get_pending_reservations(db)
    assert len(pending) == 1
    assert isinstance(pending[0], Reservation)                   # ✅ CHANGE #6


def test_approve(db):
    saved = save_reservation(SAMPLE, db)
    updated = update_reservation_status(saved.id, "approved", "OK", db)
    assert updated.status == "approved"                          # ✅ CHANGE #6: dot access
    assert updated.admin_comment == "OK"


def test_reject(db):
    saved = save_reservation(SAMPLE, db)
    updated = update_reservation_status(saved.id, "rejected", "Full", db)
    assert updated.status == "rejected"                          # ✅ CHANGE #6


def test_invalid_status(db):
    saved = save_reservation(SAMPLE, db)
    result = update_reservation_status(saved.id, "invalid", "", db)
    assert result is None