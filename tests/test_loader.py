"""Tests for the document loader."""

import json
import pytest
from src.loader import load_static_documents

SAMPLE = {
    "static": [
        {"id": "general", "text": "Test parking at 123 Main St."},
        {"id": "policies", "text": "No overnight parking."}
    ],
    "dynamic": {"working_hours": {}, "pricing": {}, "availability": []}
}


@pytest.fixture
def data_file(tmp_path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps(SAMPLE))
    return str(f)


def test_loads_correct_number_of_docs(data_file):
    docs = load_static_documents(data_file)
    assert len(docs) == 2


def test_docs_have_content_and_metadata(data_file):
    docs = load_static_documents(data_file)
    for doc in docs:
        assert len(doc.page_content) > 0
        assert "id" in doc.metadata


def test_preserves_text_content(data_file):
    docs = load_static_documents(data_file)
    texts = [d.page_content for d in docs]
    assert "123 Main St" in texts[0]