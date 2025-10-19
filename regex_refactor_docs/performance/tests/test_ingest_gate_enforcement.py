#!/usr/bin/env python3
"""
Tests for ingest gate enforcement (Safety Net 1 - Blocker 1).

Verifies that invalid artifacts abort validation with non-zero exit.
"""
import pytest
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from validate_consumer_art import validate_against_schema, ARTIFACT_SCHEMA


def test_invalid_artifact_aborts_validation():
    """Test that invalid artifact causes validation to fail."""
    invalid_artifact = {"missing_required_field": "value"}

    with pytest.raises(SystemExit) as excinfo:
        validate_against_schema(invalid_artifact, ARTIFACT_SCHEMA)

    assert excinfo.value.code == 2  # Expect exit code 2


def test_valid_artifact_passes_validation():
    """Test that valid artifact passes validation."""
    valid_artifact = {
        "org_unregistered_hits": [
            {
                "repo": "org/repo",
                "path": "foo.py",
                "pattern": "jinja2.Template"
            }
        ],
        "consumer_metadata": {
            "timestamp": "2025-10-18",
            "consumer_name": "test",
            "tool_version": "1.0"
        }
    }

    # Should not raise
    try:
        validate_against_schema(valid_artifact, ARTIFACT_SCHEMA)
    except SystemExit:
        pytest.fail("Valid artifact should not raise SystemExit")


def test_missing_org_unregistered_hits_field():
    """Test that missing org_unregistered_hits field causes failure."""
    invalid_artifact = {
        "consumer_metadata": {
            "timestamp": "2025-10-18",
            "consumer_name": "test",
            "tool_version": "1.0"
        }
    }

    with pytest.raises(SystemExit) as excinfo:
        validate_against_schema(invalid_artifact, ARTIFACT_SCHEMA)

    assert excinfo.value.code == 2


def test_missing_consumer_metadata_field():
    """Test that missing consumer_metadata field causes failure."""
    invalid_artifact = {
        "org_unregistered_hits": [
            {
                "repo": "org/repo",
                "path": "foo.py",
                "pattern": "jinja2.Template"
            }
        ]
    }

    with pytest.raises(SystemExit) as excinfo:
        validate_against_schema(invalid_artifact, ARTIFACT_SCHEMA)

    assert excinfo.value.code == 2


def test_invalid_hit_structure():
    """Test that invalid hit structure causes failure."""
    invalid_artifact = {
        "org_unregistered_hits": [
            {"path": "foo.py"}  # Missing repo and pattern
        ],
        "consumer_metadata": {
            "timestamp": "2025-10-18",
            "consumer_name": "test",
            "tool_version": "1.0"
        }
    }

    with pytest.raises(SystemExit) as excinfo:
        validate_against_schema(invalid_artifact, ARTIFACT_SCHEMA)

    assert excinfo.value.code == 2


def test_non_list_org_unregistered_hits():
    """Test that non-list org_unregistered_hits causes failure."""
    invalid_artifact = {
        "org_unregistered_hits": "not_a_list",
        "consumer_metadata": {
            "timestamp": "2025-10-18",
            "consumer_name": "test",
            "tool_version": "1.0"
        }
    }

    with pytest.raises(SystemExit) as excinfo:
        validate_against_schema(invalid_artifact, ARTIFACT_SCHEMA)

    assert excinfo.value.code == 2


def test_empty_artifact_passes():
    """Test that artifact with empty hits list passes validation."""
    valid_artifact = {
        "org_unregistered_hits": [],
        "consumer_metadata": {
            "timestamp": "2025-10-18",
            "consumer_name": "test",
            "tool_version": "1.0"
        }
    }

    # Should not raise
    try:
        validate_against_schema(valid_artifact, ARTIFACT_SCHEMA)
    except SystemExit:
        pytest.fail("Empty hits artifact should not raise SystemExit")
