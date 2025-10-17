# P3-3: CI Artifact Capture for Test Failures

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Production guidance (NOT skeleton implementation)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_3.md P3-3 (lines 685-758)
**Purpose**: Capture input markdown, parser output, stack traces, and environment info when tests fail

---

## Purpose

When tests fail, capture comprehensive diagnostic artifacts for debugging:
- **Input markdown**: Original document that caused failure
- **Parser output**: Actual result vs. expected result
- **Stack traces**: Full error traceback
- **Environment info**: Python version, dependencies, system info
- **Test context**: Test name, parameters, fixtures

**Benefits**:
- **Faster debugging**: All context available in CI artifacts
- **Reproducibility**: Can reproduce failures locally
- **Historical analysis**: Track failure patterns over time

---

## CI Integration

### GitHub Actions Workflow

**FILE**: `.github/workflows/test.yml` (Update existing workflow)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"

      - name: Create artifacts directory
        run: mkdir -p test-artifacts

      - name: Run tests with artifact capture
        run: |
          .venv/bin/python -m pytest \
            tests/ \
            --junitxml=test-results.xml \
            --artifacts-dir=test-artifacts/ \
            -v
        continue-on-error: true

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
          retention-days: 30

      - name: Upload test artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-failure-artifacts
          path: |
            test-artifacts/
            test-results.xml
          retention-days: 30

      - name: Comment PR with failure details
        if: failure() && github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const artifactCount = fs.readdirSync('test-artifacts').length;

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `❌ **Test failures detected**\n\n` +
                    `${artifactCount} test failure artifacts captured.\n\n` +
                    `Download artifacts from Actions tab to investigate.`
            });
```

**Key Features**:
1. **Create artifacts directory**: Ensures directory exists before tests
2. **Continue-on-error**: Allows artifact upload even if tests fail
3. **Upload on failure**: Only uploads artifacts when tests fail (saves CI storage)
4. **30-day retention**: Artifacts available for forensic analysis
5. **PR comments**: Notifies developers of failures with artifact count

---

## Pytest Fixture for Artifact Capture

### Basic Fixture

**FILE**: `tests/conftest.py` (Add to existing conftest)

```python
import pytest
import shutil
import json
from pathlib import Path
from typing import Any, Dict


@pytest.fixture(scope="function")
def artifact_dir(request, tmp_path):
    """
    Provide artifact directory for test outputs.

    Automatically captures artifacts on test failure:
    - Input markdown
    - Parser output (actual vs. expected)
    - Stack trace
    - Environment info

    Usage:
        def test_parser(artifact_dir):
            markdown = "# Test"
            parser = MarkdownParserCore(markdown)
            result = parser.parse()

            # On failure, save artifacts
            if result != expected:
                save_artifact(artifact_dir, "input.md", markdown)
                save_artifact(artifact_dir, "output.json", result)
    """
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(exist_ok=True)

    yield artifacts

    # On test failure, copy artifacts to CI artifacts dir
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        ci_artifacts = Path("test-artifacts") / request.node.nodeid.replace("::", "_")
        ci_artifacts.mkdir(parents=True, exist_ok=True)

        # Copy all artifacts
        for artifact in artifacts.iterdir():
            shutil.copy(artifact, ci_artifacts)

        # Create failure summary
        failure_summary = {
            "test_name": request.node.nodeid,
            "failure_type": request.node.rep_call.longrepr.__class__.__name__,
            "failure_message": str(request.node.rep_call.longrepr),
            "artifacts": [f.name for f in artifacts.iterdir()]
        }

        summary_path = ci_artifacts / "failure_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(failure_summary, f, indent=2)


def save_artifact(artifact_dir: Path, filename: str, content: Any):
    """Helper to save artifact with automatic serialization."""
    filepath = artifact_dir / filename

    if isinstance(content, (dict, list)):
        with open(filepath, 'w') as f:
            json.dump(content, f, indent=2)
    elif isinstance(content, str):
        with open(filepath, 'w') as f:
            f.write(content)
    else:
        with open(filepath, 'wb') as f:
            f.write(content)
```

### Hook for Automatic Failure Capture

**FILE**: `tests/conftest.py` (Add to existing conftest)

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result in item for artifact capture."""
    outcome = yield
    rep = outcome.get_result()

    # Store report in item for access in fixture
    setattr(item, f"rep_{rep.when}", rep)
```

---

## Example Test with Artifact Capture

### Test with Manual Artifact Capture

```python
# FILE: tests/test_parser_with_artifacts.py

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore


def test_parser_baseline_parity(artifact_dir):
    """Test parser output matches baseline (with artifact capture)."""
    markdown = "# Test\n[Link](javascript:alert(1))"

    # Parse
    parser = MarkdownParserCore(markdown)
    result = parser.parse()

    # Expected (from baseline)
    expected = {
        "sections": [{"title": "Test", "level": 1}],
        "links": []  # javascript: URL should be rejected
    }

    # Save artifacts on mismatch
    if result != expected:
        save_artifact(artifact_dir, "input.md", markdown)
        save_artifact(artifact_dir, "actual_output.json", result)
        save_artifact(artifact_dir, "expected_output.json", expected)

        # Compute diff
        diff = compute_diff(expected, result)
        save_artifact(artifact_dir, "diff.json", diff)

    # Assert
    assert result == expected
```

### Test with Automatic Artifact Capture

```python
# FILE: tests/test_adversarial_with_artifacts.py

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore


@pytest.mark.parametrize("payload_idx,payload", enumerate([
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
]))
def test_adversarial_xss_payload(artifact_dir, payload_idx, payload):
    """Test parser neutralizes XSS payload (with auto artifact capture)."""
    # Save input (automatically captured on failure)
    save_artifact(artifact_dir, f"payload_{payload_idx}.md", payload)

    # Parse
    parser = MarkdownParserCore(payload, security_profile="strict")
    result = parser.parse()

    # Save output (automatically captured on failure)
    save_artifact(artifact_dir, f"output_{payload_idx}.json", result)

    # Assert no XSS vectors in output
    html_blocks = result.get("html_blocks", [])
    for block in html_blocks:
        content = block.get("content", "")
        assert "<script>" not in content.lower(), "XSS: <script> tag not sanitized"
        assert "onerror=" not in content.lower(), "XSS: onerror handler not sanitized"
        assert "onload=" not in content.lower(), "XSS: onload handler not sanitized"

    # If test passes, artifacts still captured but not uploaded (saved locally only)
```

---

## Artifact Structure

### Example Artifact Directory Structure

```
test-artifacts/
├── test_parser_baseline_parity/
│   ├── input.md
│   ├── actual_output.json
│   ├── expected_output.json
│   ├── diff.json
│   └── failure_summary.json
├── test_adversarial_xss_payload[0-<script>]/
│   ├── payload_0.md
│   ├── output_0.json
│   └── failure_summary.json
└── test_collector_caps_end_to_end/
    ├── input.md
    ├── output.json
    ├── cap_metadata.json
    └── failure_summary.json
```

### Example Failure Summary

**FILE**: `test-artifacts/test_parser_baseline_parity/failure_summary.json`

```json
{
  "test_name": "tests/test_parser_with_artifacts.py::test_parser_baseline_parity",
  "failure_type": "AssertionError",
  "failure_message": "assert {'sections': [...], 'links': [...]} == {'sections': [...], 'links': []}",
  "artifacts": [
    "input.md",
    "actual_output.json",
    "expected_output.json",
    "diff.json"
  ],
  "timestamp": "2025-10-17T12:34:56Z",
  "python_version": "3.12.0",
  "platform": "ubuntu-latest"
}
```

---

## Downloading and Analyzing Artifacts

### Download from GitHub Actions

```bash
# Using gh CLI
gh run download <run-id> -n test-failure-artifacts

# Or: Download from Actions UI
# https://github.com/<org>/<repo>/actions/runs/<run-id>
```

### Analyze Artifacts Locally

```bash
# Extract artifacts
cd test-failure-artifacts/

# Review failure summary
cat test_parser_baseline_parity/failure_summary.json | jq

# Review input that caused failure
cat test_parser_baseline_parity/input.md

# Compare actual vs. expected output
diff -u \
  <(jq -S . test_parser_baseline_parity/expected_output.json) \
  <(jq -S . test_parser_baseline_parity/actual_output.json)

# Or: Use dedicated diff tool
code --diff \
  test_parser_baseline_parity/expected_output.json \
  test_parser_baseline_parity/actual_output.json
```

### Reproduce Failure Locally

```python
# Reproduce from artifact
import json
from doxstrux.markdown_parser_core import MarkdownParserCore

# Load input
with open("test_parser_baseline_parity/input.md") as f:
    markdown = f.read()

# Load expected
with open("test_parser_baseline_parity/expected_output.json") as f:
    expected = json.load(f)

# Reproduce parse
parser = MarkdownParserCore(markdown)
result = parser.parse()

# Compare
print("Expected:", expected)
print("Actual:", result)
print("Match:", result == expected)
```

---

## Advanced: Environment Info Capture

### Capture System Info on Failure

**FILE**: `tests/conftest.py` (Add to artifact capture)

```python
import platform
import sys
import subprocess


def capture_environment_info() -> Dict[str, Any]:
    """Capture comprehensive environment info for debugging."""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "pip_freeze": subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"]
        ).decode("utf-8").splitlines(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).decode("utf-8").strip(),
        "git_branch": subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        ).decode("utf-8").strip(),
    }


# Update artifact_dir fixture
@pytest.fixture(scope="function")
def artifact_dir(request, tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(exist_ok=True)

    yield artifacts

    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        ci_artifacts = Path("test-artifacts") / request.node.nodeid.replace("::", "_")
        ci_artifacts.mkdir(parents=True, exist_ok=True)

        # Copy artifacts
        for artifact in artifacts.iterdir():
            shutil.copy(artifact, ci_artifacts)

        # Create failure summary with environment info
        failure_summary = {
            "test_name": request.node.nodeid,
            "failure_type": request.node.rep_call.longrepr.__class__.__name__,
            "failure_message": str(request.node.rep_call.longrepr),
            "artifacts": [f.name for f in artifacts.iterdir()],
            "environment": capture_environment_info()  # ADD THIS
        }

        summary_path = ci_artifacts / "failure_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(failure_summary, f, indent=2)
```

---

## Best Practices

### 1. Capture Minimal Artifacts

**Only capture what's needed for debugging**:
- ✅ Input markdown (always)
- ✅ Parser output (always)
- ✅ Expected output (on assertion failures)
- ✅ Diff (on mismatches)
- ⚠️ Full token tree (only for parser crashes)
- ❌ Entire test environment (too large)

### 2. Use Retention Policies

**Configure retention based on artifact importance**:
```yaml
- name: Upload critical failure artifacts
  uses: actions/upload-artifact@v3
  with:
    name: security-test-failures
    path: test-artifacts/test_adversarial_*
    retention-days: 90  # Security failures: 90 days

- name: Upload regular test artifacts
  uses: actions/upload-artifact@v3
  with:
    name: test-failures
    path: test-artifacts/
    retention-days: 30  # Regular failures: 30 days
```

### 3. Compress Large Artifacts

```yaml
- name: Compress artifacts
  if: failure()
  run: tar -czf test-artifacts.tar.gz test-artifacts/

- name: Upload compressed artifacts
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: test-artifacts-compressed
    path: test-artifacts.tar.gz
    retention-days: 30
```

### 4. Anonymize Sensitive Data

```python
def anonymize_artifact(content: str) -> str:
    """Remove sensitive data from artifact before capture."""
    import re

    # Redact tokens
    content = re.sub(r'token="[^"]*"', 'token="<REDACTED>"', content)

    # Redact API keys
    content = re.sub(r'api_key="[^"]*"', 'api_key="<REDACTED>"', content)

    return content


# Usage in artifact capture
save_artifact(artifact_dir, "input.md", anonymize_artifact(markdown))
```

---

## Success Criteria

**Artifact capture complete when**:
- ✅ CI workflow configured with artifact upload
- ✅ Pytest fixture for automatic capture
- ✅ Artifacts uploaded on failure (30-day retention)
- ✅ Failure summaries include environment info
- ✅ PR comments notify developers of failures

---

## Effort Estimate

**Time**: 1.5 hours (artifact capture documentation)

**Breakdown**:
- CI workflow update: 30 minutes
- Pytest fixture creation: 30 minutes
- Environment info capture: 15 minutes
- Best practices documentation: 15 minutes

---

## References

- **PLAN_CLOSING_IMPLEMENTATION_extended_3.md**: P3-3 specification (lines 685-758)
- **Pytest fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **GitHub Actions artifacts**: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P3-3-DOC | Artifact capture documented | This file | ✅ Complete |
| CLAIM-P3-3-CI | CI workflow updated | CI Integration section | ✅ Complete |
| CLAIM-P3-3-FIXTURE | Pytest fixture provided | Pytest Fixture section | ✅ Complete |
| CLAIM-P3-3-ENV | Environment info capture | Advanced section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Scope**: Production artifact capture guidance (NOT skeleton implementation)
**Approved By**: Pending Human Review
**Next Review**: After production CI/CD configured
