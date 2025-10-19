#!/usr/bin/env python3
"""
Unit tests for Slack alert functionality in permission fallback.

Tests cover:
- Slack alert posting success
- Slack alert posting failure
- Slack webhook not configured
- Alert message format

Run with: pytest tests/test_permission_fallback_slack.py -v
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from permission_fallback import (
    _post_slack_alert,
    ensure_issue_create_permissions
)


@pytest.fixture
def mock_session():
    """Mock requests.Session for API calls."""
    session = Mock()
    return session


@pytest.fixture
def temp_artifact(tmp_path):
    """Create temporary audit artifact."""
    artifact = tmp_path / "test_audit.json"
    artifact.write_text(json.dumps({
        "org_unregistered_hits": [
            {"repo": "org/repo1", "pattern": "jinja2.Template"}
        ]
    }))
    return str(artifact)


def test_post_slack_alert_success(tmp_path):
    """Test Slack alert posts successfully."""
    fallback_path = tmp_path / "fallback_test.json"
    fallback_path.write_text("{}")

    with patch('requests.post') as mock_post:
        mock_post.return_value = Mock(status_code=200)

        success = _post_slack_alert(
            fallback_path,
            "org/repo",
            "https://hooks.slack.com/test"
        )

    assert success is True
    assert mock_post.called
    # Verify message structure
    call_args = mock_post.call_args
    message = call_args[1]["json"]
    assert "text" in message
    assert "blocks" in message
    assert "org/repo" in message["blocks"][0]["text"]["text"]


def test_post_slack_alert_failure(tmp_path):
    """Test Slack alert posting failure."""
    fallback_path = tmp_path / "fallback_test.json"
    fallback_path.write_text("{}")

    with patch('requests.post') as mock_post:
        mock_post.return_value = Mock(status_code=500)

        success = _post_slack_alert(
            fallback_path,
            "org/repo",
            "https://hooks.slack.com/test"
        )

    assert success is False


def test_post_slack_alert_exception(tmp_path):
    """Test Slack alert posting with exception."""
    fallback_path = tmp_path / "fallback_test.json"
    fallback_path.write_text("{}")

    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Network error")

        success = _post_slack_alert(
            fallback_path,
            "org/repo",
            "https://hooks.slack.com/test"
        )

    assert success is False


def test_ensure_permission_with_slack_webhook(mock_session, temp_artifact, tmp_path, monkeypatch):
    """Test fallback with Slack webhook configured."""
    monkeypatch.chdir(tmp_path)
    fallback_dir = tmp_path / "adversarial_reports"
    fallback_dir.mkdir()

    # Set Slack webhook environment variable
    monkeypatch.setenv("SLACK_WEBHOOK", "https://hooks.slack.com/test")

    # Mock user authentication success but no permission
    with patch('permission_fallback._get_authenticated_user_login', return_value="test-user"):
        with patch('permission_fallback._check_repo_write_permission', return_value=False):
            with patch('requests.post') as mock_post:
                mock_post.return_value = Mock(status_code=200)

                ok = ensure_issue_create_permissions(
                    "org/repo",
                    mock_session,
                    temp_artifact
                )

    assert ok is False
    # Verify Slack alert was attempted
    assert mock_post.called
    # Verify message content
    call_args = mock_post.call_args
    message = call_args[1]["json"]
    assert "org/repo" in str(message)


def test_ensure_permission_without_slack_webhook(mock_session, temp_artifact, tmp_path, monkeypatch):
    """Test fallback without Slack webhook configured."""
    monkeypatch.chdir(tmp_path)
    fallback_dir = tmp_path / "adversarial_reports"
    fallback_dir.mkdir()

    # Ensure SLACK_WEBHOOK is not set
    monkeypatch.delenv("SLACK_WEBHOOK", raising=False)

    # Mock user authentication success but no permission
    with patch('permission_fallback._get_authenticated_user_login', return_value="test-user"):
        with patch('permission_fallback._check_repo_write_permission', return_value=False):
            with patch('requests.post') as mock_post:
                ok = ensure_issue_create_permissions(
                    "org/repo",
                    mock_session,
                    temp_artifact
                )

    assert ok is False
    # Verify Slack alert was NOT attempted (no webhook)
    assert not mock_post.called
    # Verify fallback file still created
    fallback_files = list(fallback_dir.glob("fallback_*.json"))
    assert len(fallback_files) >= 1


def test_slack_alert_message_format(tmp_path):
    """Test Slack alert message contains required information."""
    fallback_path = tmp_path / "fallback_20250118_123456.json"
    fallback_path.write_text("{}")

    with patch('requests.post') as mock_post:
        mock_post.return_value = Mock(status_code=200)

        _post_slack_alert(
            fallback_path,
            "security/audit-backlog",
            "https://hooks.slack.com/test"
        )

    # Verify message format
    call_args = mock_post.call_args
    message = call_args[1]["json"]

    # Check top-level text
    assert "Permission Failure" in message["text"]

    # Check blocks structure
    assert len(message["blocks"]) >= 1
    block_text = message["blocks"][0]["text"]["text"]

    # Verify required information in message
    assert "security/audit-backlog" in block_text
    assert "fallback_20250118_123456.json" in block_text
    assert "Action Required" in block_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
