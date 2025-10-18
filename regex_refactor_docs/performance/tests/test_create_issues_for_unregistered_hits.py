import json
import tempfile
import hashlib
from pathlib import Path
import sys
import os

# Add tools directory to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from create_issues_for_unregistered_hits import (
    compute_hits_hash,
    suggest_code_paths_from_paths,
    group_hits,
    extract_audit_hash,
)


def test_compute_hits_hash_stable():
    """Test that hash is order-independent."""
    hits = [{"path": "a/b/c.py"}, {"path": "x/y/z.js"}]
    h1 = compute_hits_hash(hits)
    h2 = compute_hits_hash(list(reversed(hits)))
    assert h1 == h2
    assert len(h1) == 12


def test_suggest_code_paths_basic():
    """Test code paths suggestion logic."""
    paths = ["frontend/src/components/foo.js", "frontend/src/components/bar.js", "frontend/templates/main.html"]
    suggested = suggest_code_paths_from_paths(paths, top_n=3)
    # should include a frontend prefix and a dirname
    assert any("frontend" in s for s in suggested), f"Expected 'frontend' in suggestions, got: {suggested}"


def test_group_hits_local_and_org():
    """Test grouping logic for both org and local hits."""
    audit = {
        "org_unregistered_hits": [{"repo": "org/repo", "path": "a/x.py", "pattern": "jinja2.Template"}],
        "renderer_unregistered_local": [{"path": "local/path.py", "pattern": "render("}],
    }
    groups = group_hits(audit)
    assert "org/repo" in groups
    assert "<local-repo>" in groups


def test_extract_audit_hash():
    """Test audit hash extraction from issue body."""
    body = "Some text\n<!-- AUDIT-HASH: 1a2b3c -->\nMore text"
    assert extract_audit_hash(body) == "1a2b3c"
    assert extract_audit_hash("no marker here") is None
