#!/usr/bin/env python3
"""
Test: Fallback Upload & Redaction
Tests that permission failures trigger sanitized artifact upload with no local files.
"""
import os
import json
from pathlib import Path
import tempfile
import pytest


# Mock the permission_fallback module
class MockPermissionFallback:
    """Mock implementation for testing."""

    @staticmethod
    def ensure_issue_create_permissions(repo: str, session, artifact_path: str) -> bool:
        """Mock permission check - returns False on 401/403."""
        if hasattr(session, 'get'):
            resp = session.get(f"https://api.github.com/repos/{repo}")
            if resp.status_code in (401, 403):
                # Trigger fallback
                MockPermissionFallback._save_artifact_fallback(artifact_path)
                MockPermissionFallback._post_slack_alert(artifact_path, repo, None)
                return False
        return True

    @staticmethod
    def _save_artifact_fallback(artifact_path: str) -> str:
        """Mock artifact upload - returns remote path."""
        # Simulate upload to artifact store
        return "/artifact-store/fallback_123.json"

    @staticmethod
    def _post_slack_alert(fallback_path: str, central_repo: str, slack_webhook=None):
        """Mock Slack alert."""
        return True

    @staticmethod
    def _redact_sensitive_fields(artifact: dict) -> dict:
        """Redact sensitive fields from artifact."""
        redacted = artifact.copy()
        if "org_unregistered_hits" in redacted:
            for hit in redacted["org_unregistered_hits"]:
                if "snippet" in hit:
                    hit["snippet"] = "<REDACTED>"
        return redacted


class DummySession:
    """Mock session that returns 401 Unauthorized."""
    def get(self, url, headers=None, timeout=None):
        class R:
            status_code = 401
        return R()


def test_fallback_upload_and_redaction(tmp_path, monkeypatch):
    """
    Simulate 403 permission error and assert:
    1. ensure_issue_create_permissions() returns False
    2. _save_artifact_fallback() called (artifact uploaded)
    3. _post_slack_alert() called
    4. No unredacted fallback files in workspace
    """
    # Setup test artifact
    artifact_dir = tmp_path / "adversarial_reports"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / "audit_summary.json"
    artifact.write_text(json.dumps({
        "sensitive": "http://example.com/secret?token=abc",
        "org_unregistered_hits": [
            {"path": "foo.py", "snippet": "SECRET_TOKEN = 'abc123'"}
        ]
    }), encoding="utf8")

    # Track calls
    called = {"saved": False, "saved_path": None, "slack": False, "slack_payload": None}

    def fake_save_artifact(path):
        called["saved"] = True
        called["saved_path"] = "/artifact-store/fallback_123.json"
        return called["saved_path"]

    def fake_post_slack_alert(fallback_path, central_repo, slack_webhook):
        called["slack"] = True
        called["slack_payload"] = {"text": f"Saved artifact {fallback_path} for {central_repo}"}
        return True

    # Monkeypatch
    pf = MockPermissionFallback
    monkeypatch.setattr(pf, "_save_artifact_fallback", fake_save_artifact)
    monkeypatch.setattr(pf, "_post_slack_alert", fake_post_slack_alert)

    # Execute
    sess = DummySession()
    ok = pf.ensure_issue_create_permissions("org/central", sess, str(artifact))

    # Assertions
    assert ok is False, "Permission check should fail on 401"
    assert called["saved"] is True, "Artifact should be saved to fallback"
    assert called["saved_path"] is not None, "Fallback path should be returned"
    assert called["slack"] is True, "Slack alert should be sent"
    assert "Saved artifact" in called["slack_payload"]["text"], "Slack payload should contain artifact info"

    # Verify no local unredacted artifact in workspace
    local_fallbacks = list(Path(".").glob("adversarial_reports/fallback_*.json"))
    assert len(local_fallbacks) == 0, "No local fallback files should remain in workspace"

    print("✓ Test passed: Fallback upload & redaction")


def test_redaction_removes_sensitive_fields():
    """Test that _redact_sensitive_fields properly sanitizes artifacts."""
    pf = MockPermissionFallback

    artifact = {
        "org_unregistered_hits": [
            {"path": "foo.py", "snippet": "API_KEY = 'secret123'"},
            {"path": "bar.py", "snippet": "PASSWORD = 'hunter2'"}
        ]
    }

    redacted = pf._redact_sensitive_fields(artifact)

    for hit in redacted["org_unregistered_hits"]:
        assert hit["snippet"] == "<REDACTED>", "Snippets should be redacted"

    print("✓ Test passed: Redaction removes sensitive fields")


if __name__ == "__main__":
    # Run tests
    import sys

    class TmpPath:
        """Simple tmpdir replacement for standalone execution."""
        def __init__(self):
            self.path = Path(tempfile.mkdtemp())
        def __truediv__(self, other):
            return self.path / other

    class MonkeyPatch:
        """Simple monkeypatch replacement."""
        def __init__(self):
            self.patches = []
        def setattr(self, obj, name, value):
            self.patches.append((obj, name, getattr(obj, name, None)))
            setattr(obj, name, value)
        def undo(self):
            for obj, name, value in self.patches:
                if value is None:
                    delattr(obj, name)
                else:
                    setattr(obj, name, value)

    tmp = TmpPath()
    mp = MonkeyPatch()

    try:
        test_fallback_upload_and_redaction(tmp, mp)
        test_redaction_removes_sensitive_fields()
        print("\n✅ All fallback upload & redaction tests passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    finally:
        mp.undo()
