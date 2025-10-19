#!/usr/bin/env python3
"""
Tests for atomic fallback write (Safety Net - Blocker 4).

Verifies that fallback writes are atomic (no partial files).
"""
import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from permission_fallback import _save_artifact_fallback


def test_atomic_fallback_write_no_partial_files(tmp_path):
    """Test that fallback write is atomic (tmp + rename)."""
    artifact_path = tmp_path / "test_artifact.json"
    artifact_data = {
        "org_unregistered_hits": [
            {"repo": "org/repo", "path": "foo.py", "pattern": "jinja2.Template", "snippet": "sensitive code here"}
        ],
        "consumer_metadata": {"timestamp": "2025-10-18", "consumer_name": "test", "tool_version": "1.0"}
    }
    artifact_path.write_text(json.dumps(artifact_data))

    # Track rename calls
    rename_called = False
    original_rename = Path.rename

    def track_rename(self, target):
        nonlocal rename_called
        rename_called = True
        # Verify tmp file exists before rename
        assert self.exists(), f"Temp file {self} should exist before rename"
        assert self.suffix == ".tmp", f"File {self} should have .tmp suffix"
        # Perform actual rename
        original_rename(self, target)

    with patch.object(Path, "rename", track_rename):
        # Change to tmp_path for test
        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            fallback_path = _save_artifact_fallback(str(artifact_path))

            assert rename_called, "Rename should have been called"
            assert fallback_path.exists(), "Fallback file should exist"

            # Verify no tmp files left
            tmp_files = list(Path("adversarial_reports").glob("*.tmp"))
            assert len(tmp_files) == 0, f"No .tmp files should remain, found: {tmp_files}"

            # Verify content was redacted
            content = json.loads(fallback_path.read_text())
            assert content["org_unregistered_hits"][0]["snippet"] == "<REDACTED>"

        finally:
            os.chdir(old_cwd)


def test_atomic_write_creates_adversarial_reports_dir(tmp_path):
    """Test that atomic write creates adversarial_reports directory if missing."""
    artifact_path = tmp_path / "test_artifact.json"
    artifact_data = {"org_unregistered_hits": [], "consumer_metadata": {"timestamp": "2025-10-18", "consumer_name": "test", "tool_version": "1.0"}}
    artifact_path.write_text(json.dumps(artifact_data))

    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Ensure adversarial_reports doesn't exist
        reports_dir = Path("adversarial_reports")
        if reports_dir.exists():
            import shutil
            shutil.rmtree(reports_dir)

        fallback_path = _save_artifact_fallback(str(artifact_path))

        assert reports_dir.exists(), "adversarial_reports directory should be created"
        assert fallback_path.exists(), "Fallback file should exist"

    finally:
        os.chdir(old_cwd)


def test_fallback_redacts_snippets(tmp_path):
    """Test that fallback redacts sensitive snippets."""
    artifact_path = tmp_path / "test_artifact.json"
    artifact_data = {
        "org_unregistered_hits": [
            {"repo": "org/repo1", "path": "foo.py", "pattern": "jinja2.Template", "snippet": "def render():\n    template.render(data)"},
            {"repo": "org/repo2", "path": "bar.py", "pattern": "django.template", "snippet": "Template(source).render(context)"}
        ],
        "consumer_metadata": {"timestamp": "2025-10-18", "consumer_name": "test", "tool_version": "1.0"}
    }
    artifact_path.write_text(json.dumps(artifact_data))

    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        fallback_path = _save_artifact_fallback(str(artifact_path))

        # Load and verify redaction
        content = json.loads(fallback_path.read_text())
        assert content["org_unregistered_hits"][0]["snippet"] == "<REDACTED>"
        assert content["org_unregistered_hits"][1]["snippet"] == "<REDACTED>"

        # Verify original snippets are NOT in fallback file
        fallback_text = fallback_path.read_text()
        assert "def render():" not in fallback_text
        assert "Template(source).render(context)" not in fallback_text

    finally:
        os.chdir(old_cwd)


def test_fallback_preserves_metadata(tmp_path):
    """Test that fallback preserves non-sensitive metadata."""
    artifact_path = tmp_path / "test_artifact.json"
    artifact_data = {
        "org_unregistered_hits": [
            {"repo": "org/repo", "path": "foo.py", "pattern": "jinja2.Template", "snippet": "sensitive", "line_number": 42, "section_id": "sec-1"}
        ],
        "consumer_metadata": {"timestamp": "2025-10-18", "consumer_name": "test", "tool_version": "1.0"}
    }
    artifact_path.write_text(json.dumps(artifact_data))

    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        fallback_path = _save_artifact_fallback(str(artifact_path))

        content = json.loads(fallback_path.read_text())

        # Verify metadata is preserved
        hit = content["org_unregistered_hits"][0]
        assert hit["repo"] == "org/repo"
        assert hit["path"] == "foo.py"
        assert hit["pattern"] == "jinja2.Template"
        assert hit.get("line_number") == 42
        assert hit.get("section_id") == "sec-1"

        # But snippet is redacted
        assert hit["snippet"] == "<REDACTED>"

    finally:
        os.chdir(old_cwd)


def test_fallback_handles_missing_snippet_field(tmp_path):
    """Test that fallback handles hits without snippet field."""
    artifact_path = tmp_path / "test_artifact.json"
    artifact_data = {
        "org_unregistered_hits": [
            {"repo": "org/repo", "path": "foo.py", "pattern": "jinja2.Template"}  # No snippet field
        ],
        "consumer_metadata": {"timestamp": "2025-10-18", "consumer_name": "test", "tool_version": "1.0"}
    }
    artifact_path.write_text(json.dumps(artifact_data))

    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        fallback_path = _save_artifact_fallback(str(artifact_path))

        content = json.loads(fallback_path.read_text())

        # Should not crash, hit should be preserved as-is
        hit = content["org_unregistered_hits"][0]
        assert hit["repo"] == "org/repo"
        assert "snippet" not in hit

    finally:
        os.chdir(old_cwd)
