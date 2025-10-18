#!/usr/bin/env python3
"""
Unit tests for issue automation scripts (create_issues_for_unregistered_hits.py).

Tests cover:
- create_digest_issue() function with provenance metadata
- Permissions check graceful failure
- Digest issue sorting by hit count

Run with: pytest tests/test_issue_automation.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import pytest

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from create_issues_for_unregistered_hits import (
    create_digest_issue,
    check_issue_create_permission,
    TOOL_VERSION,
    ISSUE_MARKER
)


@pytest.fixture
def mock_session():
    """Mock requests.Session for GitHub API calls."""
    session = Mock()
    session.post = Mock(return_value=Mock(status_code=201, json=lambda: {"html_url": "https://github.com/org/repo/issues/1"}))
    session.get = Mock(return_value=Mock(status_code=200, json=lambda: {"permissions": {"push": True}}))
    return session


@pytest.fixture
def mock_args():
    """Mock command-line arguments."""
    args = Mock()
    args.central_repo = "security/audit-backlog"
    return args


@pytest.fixture
def audit_path(tmp_path):
    """Create temporary audit file."""
    audit_file = tmp_path / "audit.json"
    audit_file.write_text(json.dumps({"org_unregistered_hits": []}))
    return audit_file


def test_create_digest_issue_basic(mock_session, mock_args, audit_path):
    """Test digest issue creation with basic input."""
    groups = {
        "org/repo1": [{"path": "foo.py", "pattern": "jinja2.Template"}],
        "org/repo2": [{"path": "bar.py", "pattern": "django.template"}]
    }

    create_digest_issue(groups, mock_session, mock_args, audit_path)

    # Verify POST was called
    assert mock_session.post.called
    call_args = mock_session.post.call_args

    # Verify title contains repo count
    posted_json = call_args[1]["json"]
    assert "2 repos" in posted_json["title"]
    assert "unregistered" in posted_json["title"].lower()

    # Verify body contains ISSUE_MARKER
    body = posted_json["body"]
    assert ISSUE_MARKER in body


def test_create_digest_issue_sorts_by_hit_count(mock_session, mock_args, audit_path):
    """Test digest issue sorts repos by hit count (descending)."""
    groups = {
        "org/repo1": [{"path": "a.py", "pattern": "jinja2.Template"}],
        "org/repo2": [
            {"path": "b.py", "pattern": "django.template"},
            {"path": "c.py", "pattern": "render_to_string("}
        ]
    }

    create_digest_issue(groups, mock_session, mock_args, audit_path)

    body = mock_session.post.call_args[1]["json"]["body"]

    # repo2 has 2 hits, repo1 has 1 hit -> repo2 should appear first
    repo1_index = body.index("org/repo1")
    repo2_index = body.index("org/repo2")
    assert repo2_index < repo1_index, "Repos should be sorted by hit count (descending)"


def test_create_digest_issue_includes_provenance(mock_session, mock_args, audit_path):
    """Test digest issue includes provenance metadata."""
    groups = {
        "org/repo1": [{"path": "foo.py", "pattern": "jinja2.Template"}]
    }

    with patch.dict("os.environ", {"GITHUB_RUN_ID": "test-run-123"}):
        create_digest_issue(groups, mock_session, mock_args, audit_path)

    body = mock_session.post.call_args[1]["json"]["body"]

    # Verify provenance fields
    assert "Tool Version:" in body or f"**Tool Version**: {TOOL_VERSION}" in body
    assert "Run ID:" in body or "test-run-123" in body
    assert "Scan Count:" in body or "1 repos scanned" in body
    assert "Audit Run:" in body  # timestamp
    assert "Total Hits:" in body


def test_permissions_check_fails_gracefully():
    """Test permissions check fails gracefully with clear error message."""
    mock_session = Mock()
    # Simulate permission denied (push: False)
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"permissions": {"push": False, "pull": True}}
    )

    result = check_issue_create_permission("org/repo", mock_session, "fake-token")

    assert result is False, "Should return False when push permission is missing"


def test_permissions_check_handles_api_errors():
    """Test permissions check handles API errors gracefully."""
    mock_session = Mock()
    # Simulate API error
    mock_session.get.return_value = Mock(status_code=403, json=lambda: {"message": "Forbidden"})

    result = check_issue_create_permission("org/repo", mock_session, "fake-token")

    assert result is False, "Should return False on API errors"


def test_permissions_check_handles_exceptions():
    """Test permissions check handles exceptions gracefully."""
    mock_session = Mock()
    # Simulate network exception
    mock_session.get.side_effect = Exception("Network error")

    result = check_issue_create_permission("org/repo", mock_session, "fake-token")

    assert result is False, "Should return False on exceptions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
