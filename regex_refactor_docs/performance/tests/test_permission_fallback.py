#!/usr/bin/env python3
"""
Unit tests for permission fallback functionality.

Tests cover:
- Permission check with valid credentials
- Fallback when permission missing
- Fallback file creation
- Unknown permission handling

Run with: pytest tests/test_permission_fallback.py -v
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from permission_fallback import (
    ensure_issue_create_permissions,
    _get_authenticated_user_login,
    _check_repo_write_permission,
    _save_artifact_fallback
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


def test_get_authenticated_user_success(mock_session):
    """Test successful user authentication."""
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"login": "test-user"}
    )

    login = _get_authenticated_user_login(mock_session)

    assert login == "test-user"
    assert mock_session.get.called
    assert "user" in mock_session.get.call_args[0][0]


def test_get_authenticated_user_failure(mock_session):
    """Test authentication failure."""
    mock_session.get.return_value = Mock(status_code=401)

    login = _get_authenticated_user_login(mock_session)

    assert login is None


def test_check_repo_write_permission_has_permission(mock_session):
    """Test user has write permission."""
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"permission": "write"}
    )

    has_perm = _check_repo_write_permission(
        mock_session,
        "org/repo",
        "test-user"
    )

    assert has_perm is True


def test_check_repo_write_permission_no_permission(mock_session):
    """Test user lacks write permission."""
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"permission": "read"}
    )

    has_perm = _check_repo_write_permission(
        mock_session,
        "org/repo",
        "test-user"
    )

    assert has_perm is False


def test_check_repo_write_permission_not_collaborator(mock_session):
    """Test user is not a collaborator."""
    mock_session.get.return_value = Mock(status_code=404)

    has_perm = _check_repo_write_permission(
        mock_session,
        "org/repo",
        "test-user"
    )

    assert has_perm is False


def test_check_repo_write_permission_unknown(mock_session):
    """Test unknown permission status."""
    mock_session.get.return_value = Mock(status_code=500)

    has_perm = _check_repo_write_permission(
        mock_session,
        "org/repo",
        "test-user"
    )

    assert has_perm is None


def test_save_artifact_fallback(temp_artifact, tmp_path, monkeypatch):
    """Test artifact saved to fallback directory."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    fallback_dir = tmp_path / "adversarial_reports"
    fallback_dir.mkdir()

    fallback_path = _save_artifact_fallback(temp_artifact)

    assert fallback_path.exists()
    assert fallback_path.parent == fallback_dir
    assert "fallback_" in fallback_path.name

    # Verify content copied
    content = json.loads(fallback_path.read_text())
    assert "org_unregistered_hits" in content


def test_ensure_permission_success(mock_session, temp_artifact):
    """Test permission check succeeds."""
    # Mock successful user and permission check
    with patch('permission_fallback._get_authenticated_user_login', return_value="test-user"):
        with patch('permission_fallback._check_repo_write_permission', return_value=True):
            ok = ensure_issue_create_permissions(
                "org/repo",
                mock_session,
                temp_artifact
            )

    assert ok is True


def test_ensure_permission_no_user(mock_session, temp_artifact, tmp_path, monkeypatch):
    """Test fallback when user authentication fails."""
    monkeypatch.chdir(tmp_path)
    fallback_dir = tmp_path / "adversarial_reports"
    fallback_dir.mkdir()

    # Mock failed user authentication
    with patch('permission_fallback._get_authenticated_user_login', return_value=None):
        ok = ensure_issue_create_permissions(
            "org/repo",
            mock_session,
            temp_artifact
        )

    assert ok is False
    # Verify fallback file created
    fallback_files = list(fallback_dir.glob("fallback_*.json"))
    assert len(fallback_files) >= 1


def test_ensure_permission_no_permission(mock_session, temp_artifact, tmp_path, monkeypatch):
    """Test fallback when user lacks permission."""
    monkeypatch.chdir(tmp_path)
    fallback_dir = tmp_path / "adversarial_reports"
    fallback_dir.mkdir()

    # Mock user authentication success but no permission
    with patch('permission_fallback._get_authenticated_user_login', return_value="test-user"):
        with patch('permission_fallback._check_repo_write_permission', return_value=False):
            ok = ensure_issue_create_permissions(
                "org/repo",
                mock_session,
                temp_artifact
            )

    assert ok is False
    # Verify fallback file created
    fallback_files = list(fallback_dir.glob("fallback_*.json"))
    assert len(fallback_files) >= 1


def test_ensure_permission_unknown_permission(mock_session, temp_artifact, tmp_path, monkeypatch):
    """Test fallback when permission status unknown."""
    monkeypatch.chdir(tmp_path)
    fallback_dir = tmp_path / "adversarial_reports"
    fallback_dir.mkdir()

    # Mock user authentication success but unknown permission
    with patch('permission_fallback._get_authenticated_user_login', return_value="test-user"):
        with patch('permission_fallback._check_repo_write_permission', return_value=None):
            ok = ensure_issue_create_permissions(
                "org/repo",
                mock_session,
                temp_artifact
            )

    assert ok is False
    # Verify fallback file created
    fallback_files = list(fallback_dir.glob("fallback_*.json"))
    assert len(fallback_files) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
