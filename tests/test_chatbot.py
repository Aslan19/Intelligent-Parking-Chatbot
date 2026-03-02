"""Tests for chatbot graph logic (unit tests on nodes)."""

from src.chatbot import _next_missing_field, RESERVATION_FIELDS


def test_next_missing_field_empty():
    """Empty dict should return first field."""
    assert _next_missing_field({}) == "first_name"


def test_next_missing_field_partial():
    """Partially filled should return next missing."""
    data = {"first_name": "John", "last_name": "Doe"}
    assert _next_missing_field(data) == "license_plate"


def test_next_missing_field_complete():
    """Complete dict should return None."""
    data = {f: "value" for f in RESERVATION_FIELDS}
    assert _next_missing_field(data) is None


def test_all_reservation_fields_have_prompts():
    """Every required field should have a prompt message."""
    from src.chatbot import FIELD_PROMPTS
    for field in RESERVATION_FIELDS:
        assert field in FIELD_PROMPTS
        assert len(FIELD_PROMPTS[field]) > 0