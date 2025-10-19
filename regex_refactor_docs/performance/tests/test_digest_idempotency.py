#!/usr/bin/env python3
"""
Tests for digest idempotency (Safety Net - Blocker 3).

Verifies that digest creation doesn't create duplicates on retry.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from create_issues_for_unregistered_hits import create_digest_issue


class MockSession:
    """Mock requests.Session for testing."""
    def __init__(self):
        self.create_count = 0
        self.update_count = 0
        self.search_results = []

    def get(self, url, **kwargs):
        """Mock GET request."""
        resp = Mock()
        resp.headers = {"X-RateLimit-Remaining": "5000"}

        if "search/issues" in url:
            # Return search results
            resp.status_code = 200
            resp.json = lambda: {
                "total_count": len(self.search_results),
                "items": self.search_results
            }
        elif "rate_limit" in url:
            resp.status_code = 200
            resp.json = lambda: {"rate": {"remaining": 5000, "limit": 5000}}
        else:
            resp.status_code = 200
            resp.json = lambda: {}
        return resp

    def request(self, method, url, **kwargs):
        """Mock generic request."""
        resp = Mock()
        if method == "PATCH":
            # Update existing issue
            self.update_count += 1
            resp.status_code = 200
            resp.json = lambda: {"number": 1, "html_url": "https://github.com/org/repo/issues/1"}
        elif method == "POST" and "/issues" in url and "/comments" not in url:
            # Create new issue (NOT a comment)
            self.create_count += 1
            resp.status_code = 201
            resp.json = lambda: {"number": 1, "html_url": "https://github.com/org/repo/issues/1"}
        else:
            # Comment creation or other POST
            resp.status_code = 200 if "/comments" in url else 201
            resp.json = lambda: {}

        # Mock headers for rate limit
        resp.headers = {"X-RateLimit-Remaining": "5000"}
        return resp


def test_digest_creates_once_with_audit_id():
    """Test that digest with same audit_id doesn't create duplicate."""
    audit_id = "test-audit-123"
    groups = {"org/repo1": [{"path": "foo.py", "pattern": "jinja2.Template"}]}

    mock_session = MockSession()
    mock_args = Mock()
    mock_args.central_repo = "security/audit-backlog"
    audit_path = Path("test_audit.json")

    # First call - should create issue
    create_digest_issue(groups, mock_session, mock_args, audit_path, audit_id)

    assert mock_session.create_count == 1
    assert mock_session.update_count == 0

    # Simulate finding existing issue on second call
    mock_session.search_results = [{"number": 1, "html_url": "https://github.com/org/repo/issues/1", "comments_url": "https://api.github.com/repos/org/repo/issues/1/comments"}]

    # Second call - should update existing, not create new
    create_digest_issue(groups, mock_session, mock_args, audit_path, audit_id)

    # Still only 1 create, but now 1 update
    assert mock_session.create_count == 1
    assert mock_session.update_count == 1


def test_digest_generates_audit_id_if_not_provided():
    """Test that audit_id is generated if not provided."""
    groups = {"org/repo1": [{"path": "foo.py", "pattern": "jinja2.Template"}]}

    mock_session = MockSession()
    mock_args = Mock()
    mock_args.central_repo = "security/audit-backlog"
    audit_path = Path("test_audit.json")

    # Call without audit_id
    create_digest_issue(groups, mock_session, mock_args, audit_path, audit_id=None)

    # Should have created an issue
    assert mock_session.create_count == 1


def test_digest_updates_existing_issue():
    """Test that existing digest issue is updated."""
    audit_id = "test-audit-456"
    groups = {"org/repo1": [{"path": "foo.py", "pattern": "jinja2.Template"}]}

    mock_session = MockSession()
    mock_args = Mock()
    mock_args.central_repo = "security/audit-backlog"
    audit_path = Path("test_audit.json")

    # Simulate existing issue
    mock_session.search_results = [{"number": 1, "html_url": "https://github.com/org/repo/issues/1", "comments_url": "https://api.github.com/repos/org/repo/issues/1/comments"}]

    # Call should update, not create
    create_digest_issue(groups, mock_session, mock_args, audit_path, audit_id)

    assert mock_session.create_count == 0
    assert mock_session.update_count == 1


def test_digest_handles_multiple_repos():
    """Test that digest handles multiple repos correctly."""
    audit_id = "test-audit-789"
    groups = {
        "org/repo1": [{"path": "foo.py", "pattern": "jinja2.Template"}],
        "org/repo2": [{"path": "bar.py", "pattern": "django.template"}],
        "org/repo3": [{"path": "baz.py", "pattern": "render_to_string"}]
    }

    mock_session = MockSession()
    mock_args = Mock()
    mock_args.central_repo = "security/audit-backlog"
    audit_path = Path("test_audit.json")

    # Create digest
    create_digest_issue(groups, mock_session, mock_args, audit_path, audit_id)

    # Should create one digest issue
    assert mock_session.create_count == 1
    assert mock_session.update_count == 0
