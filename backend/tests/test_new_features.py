"""
Tests for the new feature services that don't require network or DB.
"""

from app.models.connection import Connection
from app.services.connection_search import _connection_text
from app.services.job_extractor import JobExtractionResult


# --- Job extractor schema validation ---

def test_job_extraction_schema_valid():
    data = {
        "company": "Acme Corp",
        "role_title": "Senior Backend Engineer",
        "seniority": "senior",
        "location": "San Francisco, CA",
        "remote_policy": "hybrid",
        "salary_range": "$200k–$240k",
        "is_genuine": True,
    }
    result = JobExtractionResult.model_validate(data)
    assert result.company == "Acme Corp"
    assert result.is_genuine is True


def test_job_extraction_schema_nulls_ok():
    """All location/salary fields are nullable -- partial extraction is valid."""
    data = {
        "company": None,
        "role_title": "Software Engineer",
        "seniority": None,
        "location": None,
        "remote_policy": None,
        "salary_range": None,
        "is_genuine": False,
    }
    result = JobExtractionResult.model_validate(data)
    assert result.is_genuine is False
    assert result.company is None


def test_job_extraction_schema_rejects_extra_fields():
    """extra='forbid' means unknown keys should raise."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        JobExtractionResult.model_validate({
            "company": "Acme",
            "role_title": "Engineer",
            "seniority": None,
            "location": None,
            "remote_policy": None,
            "salary_range": None,
            "is_genuine": True,
            "unexpected_key": "boom",
        })


# --- Connection text for embedding ---

def test_connection_text_full():
    conn = Connection(name="Jane Doe", title="Staff Engineer", company="Google")
    text = _connection_text(conn)
    assert "Jane Doe" in text
    assert "Staff Engineer" in text
    assert "Google" in text


def test_connection_text_name_only():
    conn = Connection(name="John Smith", title=None, company=None)
    text = _connection_text(conn)
    assert text == "John Smith"


def test_connection_text_no_company():
    conn = Connection(name="Alex Rivera", title="Product Manager", company=None)
    text = _connection_text(conn)
    assert "Product Manager" in text
    assert "at" not in text
