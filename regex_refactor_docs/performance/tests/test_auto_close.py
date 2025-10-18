#!/usr/bin/env python3
"""
Unit tests for auto-close functionality (auto_close_resolved_issues.py).

Tests cover:
- Conservative auto-close proposal (72h review period)
- Respecting auto-close:blocked label
- Immediate closure with auto-close:confirmed label

Run with: pytest tests/test_auto_close.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from auto_close_resolved_issues import (
    propose_auto_close,
    close_issue_immediately
)


@pytest.fixture
def mock_session():
    """Mock requests.Session for GitHub API calls."""
    session = Mock()
    session.post = Mock(return_value=Mock(status_code=201))
    session.patch = Mock(return_value=Mock(status_code=200))
    return session


@pytest.fixture
def github_token():
    """Mock GitHub token."""
    return "ghp_fake_token_123"


def test_auto_close_proposes_for_resolved_repo(mock_session, github_token):
    """Test auto-close proposes closure when repo has 0 hits (conservative mode)."""
    issue = {
        "number": 123,
        "title": "[Audit] org/repo1",
        "labels": [],
        "comments_url": "https://api.github.com/repos/security/audit-backlog/issues/123/comments",
        "url": "https://api.github.com/repos/security/audit-backlog/issues/123"
    }

    reason = "Latest audit shows 0 unregistered hits for org/repo1"

    propose_auto_close(issue, reason, mock_session, github_token)

    # Verify comment was posted
    assert mock_session.post.called
    comment_call = mock_session.post.call_args
    assert "Proposed Auto-Close" in comment_call[1]["json"]["body"]
    assert "72 hours" in comment_call[1]["json"]["body"]

    # Verify auto-close:proposed label was added
    assert mock_session.patch.called
    patch_call = mock_session.patch.call_args
    assert "auto-close:proposed" in patch_call[1]["json"]["labels"]


def test_auto_close_respects_blocked_label(mock_session, github_token):
    """Test auto-close skips issues with auto-close:blocked label."""
    issue = {
        "number": 123,
        "title": "[Audit] org/repo1",
        "labels": [{"name": "auto-close:blocked"}],
        "comments_url": "https://api.github.com/repos/security/audit-backlog/issues/123/comments",
        "url": "https://api.github.com/repos/security/audit-backlog/issues/123"
    }

    reason = "Latest audit shows 0 unregistered hits for org/repo1"

    propose_auto_close(issue, reason, mock_session, github_token)

    # Verify no API calls were made (blocked label prevents action)
    assert not mock_session.post.called
    assert not mock_session.patch.called


def test_auto_close_skips_already_proposed(mock_session, github_token):
    """Test auto-close skips issues that already have auto-close:proposed label."""
    issue = {
        "number": 123,
        "title": "[Audit] org/repo1",
        "labels": [{"name": "auto-close:proposed"}],
        "comments_url": "https://api.github.com/repos/security/audit-backlog/issues/123/comments",
        "url": "https://api.github.com/repos/security/audit-backlog/issues/123"
    }

    reason = "Latest audit shows 0 unregistered hits for org/repo1"

    propose_auto_close(issue, reason, mock_session, github_token)

    # Verify no new API calls were made (already proposed)
    assert not mock_session.post.called
    assert not mock_session.patch.called


def test_auto_close_confirmed_closes_immediately(mock_session, github_token):
    """Test auto-close closes immediately when auto-close:confirmed label is present."""
    issue = {
        "number": 123,
        "title": "[Audit] org/repo1",
        "labels": [{"name": "auto-close:confirmed"}],
        "comments_url": "https://api.github.com/repos/security/audit-backlog/issues/123/comments",
        "url": "https://api.github.com/repos/security/audit-backlog/issues/123"
    }

    reason = "Latest audit shows 0 unregistered hits for org/repo1"

    propose_auto_close(issue, reason, mock_session, github_token)

    # Verify issue was closed immediately (comment + state change)
    assert mock_session.post.called  # Comment posted
    comment_call = mock_session.post.call_args
    assert "Auto-closing: Issue resolved" in comment_call[1]["json"]["body"]

    assert mock_session.patch.called  # Issue state changed to closed
    patch_call = mock_session.patch.call_args
    assert patch_call[1]["json"]["state"] == "closed"


def test_close_issue_immediately(mock_session, github_token):
    """Test close_issue_immediately function posts comment and closes issue."""
    issue = {
        "number": 456,
        "title": "[Audit] org/repo2",
        "labels": [],
        "comments_url": "https://api.github.com/repos/security/audit-backlog/issues/456/comments",
        "url": "https://api.github.com/repos/security/audit-backlog/issues/456"
    }

    reason = "Confirmed resolved by manual review"

    close_issue_immediately(issue, reason, mock_session, github_token, pr_number="789")

    # Verify comment was posted
    assert mock_session.post.called
    comment_call = mock_session.post.call_args
    comment_body = comment_call[1]["json"]["body"]
    assert "Auto-closing: Issue resolved" in comment_body
    assert reason in comment_body
    assert "PR #789" in comment_body

    # Verify issue was closed
    assert mock_session.patch.called
    patch_call = mock_session.patch.call_args
    assert patch_call[1]["json"]["state"] == "closed"


def test_propose_auto_close_includes_action_instructions(mock_session, github_token):
    """Test that proposed auto-close comment includes action instructions."""
    issue = {
        "number": 123,
        "title": "[Audit] org/repo1",
        "labels": [],
        "comments_url": "https://api.github.com/repos/security/audit-backlog/issues/123/comments",
        "url": "https://api.github.com/repos/security/audit-backlog/issues/123"
    }

    reason = "Latest audit shows 0 unregistered hits"

    propose_auto_close(issue, reason, mock_session, github_token)

    comment_body = mock_session.post.call_args[1]["json"]["body"]

    # Verify action instructions are present
    assert "auto-close:confirmed" in comment_body
    assert "auto-close:blocked" in comment_body
    assert "auto-close:proposed" in comment_body


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
