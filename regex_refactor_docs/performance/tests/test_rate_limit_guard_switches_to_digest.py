#!/usr/bin/env python3
"""
Test: Rate-Limit Guard Switches to Digest
Tests that low GitHub API quota triggers digest-only mode.
"""
import sys
from pathlib import Path
from unittest.mock import Mock
import pytest

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from create_issues_for_unregistered_hits import check_rate_limit, GITHUB_QUOTA_THRESHOLD


def test_rate_limit_guard_switches_to_digest_when_low():
    """
    Mock low quota and assert switch to digest-only mode.

    Tests:
    1. check_rate_limit() returns True when quota >= threshold (500)
    2. check_rate_limit() returns False when quota < threshold
    """
    # Test high quota (OK to proceed)
    class HighQuotaSession:
        def get(self, url, **kwargs):
            r = Mock()
            r.status_code = 200
            r.json = lambda: {
                "rate": {
                    "remaining": 5000,
                    "limit": 5000
                }
            }
            return r

    session_high = HighQuotaSession()
    result_high = check_rate_limit(session_high)

    assert result_high is True, "High quota should return True (proceed with individual issues)"
    print("✓ High quota (5000) -> proceed with individual issues")

    # Test low quota (force digest mode)
    class LowQuotaSession:
        def get(self, url, **kwargs):
            r = Mock()
            r.status_code = 200
            r.json = lambda: {
                "rate": {
                    "remaining": 100,  # Below threshold of 500
                    "limit": 5000
                }
            }
            return r

    session_low = LowQuotaSession()
    result_low = check_rate_limit(session_low)

    assert result_low is False, "Low quota should return False (force digest mode)"
    print("✓ Low quota (100) -> force digest mode")


def test_rate_limit_guard_threshold_at_boundary():
    """Test behavior at exact threshold boundary."""
    # At threshold (500)
    class ThresholdSession:
        def get(self, url, **kwargs):
            r = Mock()
            r.status_code = 200
            r.json = lambda: {
                "rate": {
                    "remaining": GITHUB_QUOTA_THRESHOLD,  # Exactly at threshold
                    "limit": 5000
                }
            }
            return r

    session_threshold = ThresholdSession()
    result = check_rate_limit(session_threshold)

    # At threshold should still be OK (not less than)
    assert result is True, f"At threshold ({GITHUB_QUOTA_THRESHOLD}) should return True"
    print(f"✓ At threshold ({GITHUB_QUOTA_THRESHOLD}) -> proceed")

    # Just below threshold (499)
    class BelowThresholdSession:
        def get(self, url, **kwargs):
            r = Mock()
            r.status_code = 200
            r.json = lambda: {
                "rate": {
                    "remaining": GITHUB_QUOTA_THRESHOLD - 1,
                    "limit": 5000
                }
            }
            return r

    session_below = BelowThresholdSession()
    result_below = check_rate_limit(session_below)

    assert result_below is False, f"Below threshold ({GITHUB_QUOTA_THRESHOLD - 1}) should return False"
    print(f"✓ Below threshold ({GITHUB_QUOTA_THRESHOLD - 1}) -> force digest")


def test_rate_limit_exhausted_returns_false():
    """Test that exhausted quota forces digest mode (doesn't crash)."""
    class ExhaustedSession:
        def get(self, url, **kwargs):
            r = Mock()
            r.status_code = 200
            r.json = lambda: {
                "rate": {
                    "remaining": 0,  # Exhausted
                    "limit": 5000,
                    "reset": 1234567890
                }
            }
            return r

    session = ExhaustedSession()
    result = check_rate_limit(session)

    # Should return False (force digest) rather than crash
    # This is safer - the low quota check catches it first
    assert result is False, "Exhausted quota should return False (force digest mode)"
    print("✓ Exhausted quota (0) -> force digest mode")


def test_rate_limit_api_failure_proceeds_with_caution():
    """Test that API failure allows proceeding (fail-open for rate limit check)."""
    class FailedSession:
        def get(self, url, **kwargs):
            r = Mock()
            r.status_code = 500  # API failure
            return r

    session = FailedSession()
    result = check_rate_limit(session)

    # Should proceed with caution (fail-open)
    assert result is True, "API failure should return True (proceed with caution)"
    print("✓ API failure -> proceed with caution")


if __name__ == "__main__":
    try:
        test_rate_limit_guard_switches_to_digest_when_low()
        test_rate_limit_guard_threshold_at_boundary()
        test_rate_limit_exhausted_returns_false()
        test_rate_limit_api_failure_proceeds_with_caution()

        print("\n✅ All rate-limit guard tests passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
