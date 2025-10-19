#!/usr/bin/env python3
"""
Tests for GitHub API rate-limit guard (Safety Net - Blocker 5).

Verifies that rate-limit check switches to digest mode when quota low.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from create_issues_for_unregistered_hits import check_rate_limit


def test_rate_limit_ok_when_quota_high():
    """Test that rate limit check returns True when quota is high."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rate": {"remaining": 4000, "limit": 5000}}
    mock_session.get.return_value = mock_resp

    result = check_rate_limit(mock_session)

    assert result is True


def test_rate_limit_forces_digest_when_low():
    """Test that low API quota forces digest mode."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rate": {"remaining": 300, "limit": 5000}}
    mock_session.get.return_value = mock_resp

    result = check_rate_limit(mock_session)

    assert result is False  # Should force digest mode


def test_rate_limit_aborts_when_exhausted():
    """Test that exhausted quota aborts with exit code 3."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rate": {"remaining": 0, "limit": 5000, "reset": 1234567890}}
    mock_session.get.return_value = mock_resp

    with pytest.raises(SystemExit) as excinfo:
        check_rate_limit(mock_session)

    assert excinfo.value.code == 3


def test_rate_limit_threshold_boundary():
    """Test behavior at exact threshold (500)."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rate": {"remaining": 500, "limit": 5000}}
    mock_session.get.return_value = mock_resp

    result = check_rate_limit(mock_session)

    # At threshold (500), should still be OK
    assert result is True


def test_rate_limit_just_below_threshold():
    """Test behavior just below threshold (499)."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rate": {"remaining": 499, "limit": 5000}}
    mock_session.get.return_value = mock_resp

    result = check_rate_limit(mock_session)

    # Below threshold, should force digest
    assert result is False


def test_rate_limit_api_failure_proceeds_with_caution():
    """Test that API failure allows proceeding with caution."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 500  # Server error
    mock_session.get.return_value = mock_resp

    result = check_rate_limit(mock_session)

    # Should proceed with caution (return True)
    assert result is True


def test_rate_limit_exception_proceeds_with_caution():
    """Test that exception allows proceeding with caution."""
    mock_session = Mock()
    mock_session.get.side_effect = Exception("Network error")

    result = check_rate_limit(mock_session)

    # Should proceed with caution (return True)
    assert result is True


def test_rate_limit_calls_correct_endpoint():
    """Test that rate limit check calls the correct API endpoint."""
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rate": {"remaining": 4000, "limit": 5000}}
    mock_session.get.return_value = mock_resp

    check_rate_limit(mock_session)

    # Verify correct endpoint was called
    mock_session.get.assert_called_once()
    args, kwargs = mock_session.get.call_args
    assert args[0] == "https://api.github.com/rate_limit"
    assert "timeout" in kwargs
