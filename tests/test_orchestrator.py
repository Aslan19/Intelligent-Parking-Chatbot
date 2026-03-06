from src.orchestrator import _next_missing, FIELDS, PROMPTS


def test_next_missing_empty():
    assert _next_missing({}) == "first_name"


def test_next_missing_partial():
    assert _next_missing({"first_name": "A", "last_name": "B"}) == "license_plate"


def test_next_missing_complete():
    assert _next_missing({f: "x" for f in FIELDS}) is None


def test_all_fields_have_prompts():
    for f in FIELDS:
        assert f in PROMPTS


def test_pipeline_state_accepts_keys():
    from src.orchestrator import PipelineState
    state: PipelineState = {"user_message": "hi", "mode": "user"}
    assert state["mode"] == "user"