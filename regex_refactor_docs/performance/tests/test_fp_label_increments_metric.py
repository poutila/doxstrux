#!/usr/bin/env python3
"""
Test: FP Label → Metric Increment
Tests that audit-fp labeled issues are counted and pushed to Pushgateway.
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock
import pytest

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from fp_metric_worker import sync_audit_fp_to_metric, get_audit_fp_count, export_metric


class FakeSession:
    """Mock session that returns fake GitHub API responses."""
    def __init__(self, fp_count=2):
        self.fp_count = fp_count

    def get(self, url, headers=None, timeout=None, params=None):
        """Mock GitHub Search API response."""
        class R:
            status_code = 200

            def json(self):
                return {
                    "total_count": self.fp_count,
                    "items": [
                        {"number": i, "title": f"Issue {i}"}
                        for i in range(1, self.fp_count + 1)
                    ]
                }

        r = R()
        r.fp_count = self.fp_count
        return r


def test_fp_label_increments_metric(monkeypatch):
    """
    Apply audit-fp label and assert metric incremented.

    Tests:
    1. sync_audit_fp_to_metric() queries GitHub for issues labeled audit-fp
    2. Metric pushed to Pushgateway
    3. Payload contains audit_fp_marked_total with correct count
    """
    fake_issues_count = 3
    session = FakeSession(fp_count=fake_issues_count)

    pushed = {"called": False, "payload": None, "url": None}

    def fake_pushgateway_put(url, data, headers=None, timeout=None):
        """Mock Pushgateway PUT request."""
        pushed["called"] = True
        pushed["payload"] = data
        pushed["url"] = url

        class R:
            status_code = 200
            def raise_for_status(self):
                pass

        return R()

    # Monkeypatch requests.put
    import requests
    monkeypatch.setattr(requests, "put", fake_pushgateway_put)

    # Execute
    sync_audit_fp_to_metric(
        "org/central",
        "http://pushgateway:9091",
        session=session
    )

    # Assertions
    assert pushed["called"] is True, "Pushgateway PUT should be called"
    assert pushed["payload"] is not None, "Payload should be sent"
    assert b"audit_fp_marked_total" in pushed["payload"], "Payload should contain metric name"
    assert b"audit_fp_marked_total 3" in pushed["payload"], f"Payload should contain count {fake_issues_count}"
    assert "audit_fp_sync" in pushed["url"], "URL should contain job name"

    print("✓ Test passed: FP label increments metric")


def test_get_audit_fp_count():
    """Test that get_audit_fp_count queries GitHub correctly."""
    session = FakeSession(fp_count=5)
    count = get_audit_fp_count("org/repo", session)

    assert count == 5, f"Should return 5, got {count}"
    print("✓ Test passed: get_audit_fp_count")


def test_export_metric_formats_correctly(monkeypatch):
    """Test that export_metric formats Prometheus exposition correctly."""
    pushed = {"data": None}

    def fake_put(url, data, headers=None, timeout=None):
        pushed["data"] = data
        class R:
            status_code = 200
            def raise_for_status(self):
                pass
        return R()

    import requests
    monkeypatch.setattr(requests, "put", fake_put)

    export_metric("http://pushgateway:9091", "test_job", 42)

    assert pushed["data"] is not None
    assert b"# TYPE audit_fp_marked_total gauge" in pushed["data"]
    assert b"audit_fp_marked_total 42" in pushed["data"]

    print("✓ Test passed: export_metric formats correctly")


def test_zero_fp_issues(monkeypatch):
    """Test that worker handles zero FP issues correctly."""
    session = FakeSession(fp_count=0)

    pushed = {"called": False, "payload": None}

    def fake_put(url, data, headers=None, timeout=None):
        pushed["called"] = True
        pushed["payload"] = data
        class R:
            status_code = 200
            def raise_for_status(self):
                pass
        return R()

    import requests
    monkeypatch.setattr(requests, "put", fake_put)

    sync_audit_fp_to_metric(
        "org/repo",
        "http://pushgateway:9091",
        session=session
    )

    assert pushed["called"] is True
    assert b"audit_fp_marked_total 0" in pushed["payload"]

    print("✓ Test passed: zero FP issues")


if __name__ == "__main__":
    import sys

    class MonkeyPatch:
        """Simple monkeypatch replacement."""
        def __init__(self):
            self.patches = []

        def setattr(self, obj, name, value):
            original = getattr(obj, name, None)
            self.patches.append((obj, name, original))
            setattr(obj, name, value)

        def undo(self):
            for obj, name, original in self.patches:
                if original is None:
                    delattr(obj, name)
                else:
                    setattr(obj, name, original)

    mp = MonkeyPatch()

    try:
        test_fp_label_increments_metric(mp)
        mp.undo()
        mp = MonkeyPatch()

        test_get_audit_fp_count()
        mp.undo()
        mp = MonkeyPatch()

        test_export_metric_formats_correctly(mp)
        mp.undo()
        mp = MonkeyPatch()

        test_zero_fp_issues(mp)
        mp.undo()

        print("\n✅ All FP label → metric tests passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        mp.undo()
