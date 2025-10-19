---
title: "Detailed Task List - Phase 8 Security Hardening"
version: "3.0"
document_id: "phase8-security-hardening-detailed-task-list"
created: "2025-10-18"
owner: "Security & SRE Teams"
audience:
  - dev
  - sre
  - security
metadata:
  project_full_name: "Token Warehouse Security Hardening & Performance Optimization"
  status: "Production-Ready Canary"
  total_phases: 5
  schema_version: "1.0"
---

# Detailed Task List - Phase 8 Security Hardening

**Project**: Token Warehouse Security Hardening & Performance Optimization
**Date**: 2025-10-18
**Version**: 3.0
**Status**: Production-Ready Canary

> **Note**: This document is available in multiple formats:
> - **Markdown** (this file): Human-readable with {{PLACEHOLDER}} tokens
> - **YAML**: `DETAILED_TASK_LIST_template.yaml` - Machine-readable YAML format
> - **JSON**: `DETAILED_TASK_LIST_template.json` - Machine-readable JSON format
>
> Use `tools/render_template.py` to render templates with actual values.

---

## Overview

**Goal**: Ship 5 mandatory safety nets with 4 behavioral tests and 48-hour canary monitoring

**Success Criteria**:
- All 5 safety nets verified and functional (S1, S2, R1, R2, C1)
- All 4 behavioral tests passing with 100% pass rate (14/14 sub-tests)
- Green-light audit exits with code 0 and 48-hour clean canary run

**Total Estimated Time**: 90 minutes implementation + 48 hours monitoring

**Phases**: 5 phases (Phase 0 through Phase 4)

---

## Phase Unlock Mechanism

**Enforcement**: Each phase N+1 cannot start until `.phase-1.complete.json` exists for phase N.

### Phase Unlock Artifact Schema

```json
{
  "schema_version": "1.0",
  "min_schema_version": "1.0",
  "phase": 1,
  "phase_name": "{{PHASE_NAME}}",
  "baseline_pass_count": 14/14,
  "ci_gates_passed": ["G1", "G2", "G3", "G4", "G5"],
  "safety_nets_count_before": {{VALUE_BEFORE}},
  "safety_nets_count_after": {{VALUE_AFTER}},
  "performance_delta_median": "N/A (no performance regression expected)",
  "performance_delta_p95": "N/A (security hardening, not performance optimization)",
  "git_commit": "HEAD",
  "completion_date": "2025-10-18",
  "evidence_blocks": [
    {
      "evidence_id": "{{EVIDENCE_ID}}",
      "file": "{{FILE_PATH}}",
      "lines": "{{LINE_RANGE}}"
    }
  ]
}
```

**Fields**:
- `schema_version`: "1.0" (constant)
- `min_schema_version`: "1.0" (constant)
- `phase`: Phase number (0-4)
- `phase_name`: Descriptive name (e.g., "{{EXAMPLE_PHASE_NAME}}")
- `baseline_pass_count`: Number of baseline tests passed
- `ci_gates_passed`: Array of CI gate identifiers that passed
- `safety_nets_count_before`: Metric value before phase
- `safety_nets_count_after`: Metric value after phase
- `performance_delta_median`: Median performance change (e.g., "+2.3%")
- `performance_delta_p95`: P95 performance change (e.g., "+4.1%")
- `git_commit`: Full git commit hash
- `completion_date`: ISO8601 timestamp
- `evidence_blocks`: Array of evidence references

### Phase Unlock Enforcement

**Validation command**:
```bash
# Example validation in CI
if [ ! -f ".phase-0.complete.json" ]; then
    echo "Error: Phase 0 not complete. Cannot start Phase {{CURRENT_PHASE}}."
    exit 1
fi

# Validate schema
python3 tools/validate_phase_artifact.py .phase-0.complete.json || exit 1
```

**CI integration**:
```yaml
# .github/workflows/{{WORKFLOW_NAME}}.yml
jobs:
  phase-1:
    steps:
      - name: Verify previous phase complete
        run: |
          python3 tools/validate_phase_artifact.py .phase-0.complete.json
```

---

## Environment Variables Reference

All scripts and CI gates use these environment variables for consistency:

```bash
export {{PROJECT_ENV_VAR_1}}="false"
export {{PROJECT_ENV_VAR_2}}="10"
export {{PROJECT_ENV_VAR_3}}="${{ secrets.GITHUB_TOKEN }}"
```

**Required variables**:
- `POLICY_REQUIRE_HMAC`: When 'true', ingest gate rejects unsigned artifacts (exit 2)
- `MAX_ISSUES_PER_RUN`: Maximum GitHub issues created per audit run (digest cap)
- `GITHUB_TOKEN`: GitHub API token for issue creation and branch protection queries

---

## Global Utilities

### Subprocess Timeout Helper

**File**: `tools/subprocess_timeout.py`

Prevents indefinite hangs in CI:

```python
import subprocess
import sys
from typing import List, Optional

def run_with_timeout(
    cmd: List[str],
    timeout_seconds: int = 600,
    cwd: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Run subprocess with timeout enforcement.

    Args:
        cmd: Command and arguments as list
        timeout_seconds: Maximum execution time (default: 600)
        cwd: Working directory (default: None)

    Returns:
        CompletedProcess instance

    Raises:
        subprocess.TimeoutExpired: If command exceeds timeout
        subprocess.CalledProcessError: If command exits non-zero
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=cwd,
            check=True
        )
        return result
    except subprocess.TimeoutExpired as e:
        print(f"Command timed out after {timeout_seconds}s: {' '.join(cmd)}", file=sys.stderr)
        raise
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {' '.join(cmd)}", file=sys.stderr)
        print(f"STDOUT: {e.stdout}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        raise

if __name__ == "__main__":
    # Example usage
    result = run_with_timeout(["{{EXAMPLE_COMMAND}}", "{{EXAMPLE_ARG}}"], timeout_seconds=30)
    print(result.stdout)
```

**Usage**:
```python
from tools.subprocess_timeout import run_with_timeout

# With timeout enforcement
result = run_with_timeout(
    ["{{COMMAND}}", "{{ARG1}}", "{{ARG2}}"],
    timeout_seconds={{TIMEOUT_VALUE}}
)
```

### Atomic File Write Utility

**File**: `tools/atomic_write.py`

Prevents partial writes and race conditions:

```python
import os
import tempfile
from pathlib import Path

def atomic_write_text(path: Path, data: str, encoding: str = "utf-8") -> None:
    """Atomic file write with tmpfile + rename.

    Args:
        path: Target file path
        data: Content to write
        encoding: Text encoding (default: utf-8)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        text=True
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as f:
            f.write(data)
        os.replace(tmp, path)  # Atomic on POSIX/Windows
    finally:
        try:
            os.remove(tmp)
        except FileNotFoundError:
            pass
```

**Usage**:
```python
from tools.atomic_write import atomic_write_text
from pathlib import Path
import json

# Phase unlock artifacts (whole-file replace)
atomic_write_text(Path(".phase-1.complete.json"), json.dumps(artifact, indent=2))

# IMPORTANT: For JSONL append (evidence blocks), DO NOT use atomic_write_text
# Use the portalocker-based appender in tools/create_evidence_block.py instead
# Rationale: read+concat+replace races between parallel writers; use O_APPEND + lock
# See "Evidence Utility Script" section below for correct pattern
```

---

### Schema Version Validator

**File**: `tools/validate_phase_artifact.py`

Validates phase unlock artifacts before allowing Phase N+1 to start:

```python
import json
import sys
from pathlib import Path

class SecurityError(RuntimeError):
    pass

REQUIRED_SCHEMA = {
    "schema_version": "1.0",
    "min_schema_version": "1.0"
}

def validate_artifact(artifact_path: Path) -> dict:
    """Validate phase unlock artifact schema.

    Args:
        artifact_path: Path to .phase-N.complete.json

    Returns:
        Validated artifact dict

    Raises:
        SecurityError: On validation failure
    """
    if not artifact_path.exists():
        raise SecurityError(f"Artifact not found: {artifact_path}")

    data = json.loads(artifact_path.read_text(encoding="utf-8"))

    # Schema version check
    for key, expected_value in REQUIRED_SCHEMA.items():
        actual_value = data.get(key)
        if actual_value != expected_value:
            raise SecurityError(
                f"{key} mismatch: {actual_value} != {expected_value}"
            )

    # Required keys
    required_keys = [
        "phase", "baseline_pass_count", "ci_gates_passed",
        "git_commit", "schema_version", "min_schema_version"
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise SecurityError(f"Missing required keys: {missing}")

    return data

if __name__ == "__main__":
    try:
        artifact = validate_artifact(Path(sys.argv[1]))
        print(json.dumps({"status": "OK", "phase": artifact["phase"]}))
        sys.exit(0)
    except SecurityError as e:
        print(json.dumps({"status": "FAIL", "reason": str(e)}))
        sys.exit(1)
```

**Usage**:
```bash
# Validate before starting Phase 1
python3 tools/validate_phase_artifact.py .phase-0.complete.json
```

---

### Evidence Utility Script

**File**: `tools/create_evidence_block.py`

Centralized evidence block creation with truly atomic append via portalocker:

```python
from pathlib import Path
import json
import sys
import hashlib
from datetime import datetime

# Requires: pip install portalocker
try:
    import portalocker
except ImportError:
    raise ImportError(
        "portalocker required for atomic evidence append. "
        "Install with: pip install portalocker"
    )

class SecurityError(RuntimeError):
    """Security validation failure."""
    pass

def create_evidence_block(
    evidence_id: str,
    phase: int,
    file: str,
    lines: str,
    description: str
) -> str:
    """Create evidence block with truly atomic append.

    Uses portalocker for cross-platform file locking with O_APPEND.
    Prevents race conditions in parallel CI jobs.

    Snippets truncated to 1000 chars after redaction to minimize
    secret leakage while preserving audit context.

    Args:
        evidence_id: Unique identifier
        phase: Phase number (0-4)
        file: Source file path
        lines: Line range (e.g., "450-475")
        description: Change description

    Returns:
        evidence_id on success

    Raises:
        SecurityError: On file read, write failure, or timeout
    """
    # Read source with explicit encoding
    file_path = Path(file)
    if not file_path.exists():
        raise SecurityError(f"Evidence file not found: {file}")

    content = file_path.read_text(encoding="utf-8")

    # Extract line range
    start, end = map(int, lines.split("-"))
    snippet_lines = content.split("\n")[start-1:end]
    snippet = "\n".join(snippet_lines)

    # Compute hash over FULL snippet (before redaction/truncation)
    sha256 = hashlib.sha256(snippet.encode("utf-8")).hexdigest()

    # Redact probable secrets before truncation
    snippet = _redact_secrets(snippet)

    # Truncate for storage (prevents secret leakage)
    # 1000 chars post-redaction captures context without exposing full tokens/keys
    truncated_snippet = snippet[:1000]

    # Create evidence block
    evidence = {
        "evidence_id": evidence_id,
        "phase": phase,
        "file": file,
        "lines": lines,
        "description": description,
        "code_snippet": truncated_snippet,
        "sha256": sha256,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Truly atomic append with portalocker
    # - O_APPEND ensures atomic writes even from multiple processes
    # - LOCK_EX provides exclusive lock during write
    # - timeout=10 prevents indefinite hangs
    evidence_file = Path("evidence_blocks.jsonl")
    evidence_file.parent.mkdir(parents=True, exist_ok=True)

    with portalocker.Lock(
        evidence_file,
        mode="a",
        timeout=10,
        flags=portalocker.LOCK_EX
    ) as f:
        f.write(json.dumps(evidence, ensure_ascii=False) + "\n")

    return evidence_id


def _redact_secrets(snippet: str) -> str:
    """Remove probable secrets before truncation.

    Patterns:
    - Long base64-like strings (40+ chars)
    - token=, key=, secret=, password=, auth= patterns
    - API keys, tokens in common formats

    Preserves code structure while removing sensitive values.
    """
    import re

    # Remove long base64-like strings
    snippet = re.sub(r'[A-Za-z0-9+/]{40,}={0,2}', '<REDACTED_BASE64>', snippet)

    # Remove token/key/secret patterns
    snippet = re.sub(
        r'\b(token|key|secret|password|auth|api_key|api_secret)\s*[=:]\s*["\']?[\w\-_+/]{20,}["\']?',
        r'\1=<REDACTED>',
        snippet,
        flags=re.IGNORECASE
    )

    # Remove bearer tokens
    snippet = re.sub(r'Bearer\s+[\w\-_+/\.]{20,}', 'Bearer <REDACTED>', snippet, flags=re.IGNORECASE)

    return snippet


if __name__ == "__main__":
    # Read JSON from stdin
    try:
        block_data = json.load(sys.stdin)
        evidence_id = create_evidence_block(**block_data)
        print(json.dumps({"status": "OK", "evidence_id": evidence_id}))
        sys.exit(0)
    except SecurityError as e:
        print(json.dumps({"status": "FAIL", "reason": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "FAIL", "reason": f"Unexpected error: {e}"}), file=sys.stderr)
        sys.exit(1)
```

**Usage**:
```bash
# Create evidence block
echo '{"evidence_id":"{{EVIDENCE_ID}}","phase":1,"file":"{{FILE_PATH}}","lines":"{{LINE_RANGE}}","description":"{{DESCRIPTION}}"}' \
  | python3 tools/create_evidence_block.py
```

**Installation**:
```bash
# Install portalocker dependency
pip install portalocker
```

---

## Global Test Macros and Symbols

### Test Commands

- **§TEST_FAST**: `bash tools/run_5_tests.sh` (~~2 minutes, 5 files)
- **§TEST_FULL**: `.venv/bin/python -m pytest tests/ -v` (~~5 minutes, all files)
- **§TEST_PERF**: `python tools/capture_baseline_metrics.py --auto --out /tmp/metrics.json` (performance validation)
- **§CI_ALL**: Sequential gate execution (G1→G5, explicit order required):
  ```bash
  bash tools/verify_5_guards.sh && \
  .venv/bin/python -m pytest tests/test_*.py -v && \
  python tools/audit_greenlight.py --report /tmp/audit.json && \
  grep -r 'POLICY_REQUIRE_HMAC' .github/workflows/ && \
  ls -la prometheus/rules/audit_rules.yml .github/workflows/ingest_and_dryrun.yml
  ```
  **Rationale**: Explicit list prevents glob reordering and enforces G1→G5 dependency chain

### Corpus Metadata

- **§CORPUS_COUNT**: Dynamic corpus count (cross-platform, Python-only)
  ```python
  from pathlib import Path
  corpus_count = len(list(Path("adversarial_corpora").rglob("*.json")))
  ```
  - **Computed at runtime** - no hardcoded values in code
  - Current baseline: dynamic (originally 9 files)
  - **Policy**: ALWAYS use Python version for cross-platform compatibility (Windows, Linux, macOS)
  - **Never use bash `find` commands** - they fail on Windows and mishandle spaces in filenames

**Example usage in scripts**:
```python
# Good - cross-platform
from pathlib import Path

def get_corpus_count() -> int:
    """Get current corpus count (dynamic, cross-platform)."""
    return len(list(Path("adversarial_corpora").rglob("*.json")))

# In validation
corpus_count = get_corpus_count()
print(f"Testing {corpus_count} {{FILE_TYPE}} files")
```

**Forbidden patterns**:
```bash
# BAD - Linux/Mac only, fails on Windows
CORPUS_COUNT=$(find adversarial_corpora -name "*.json" | wc -l)

# BAD - breaks on filenames with spaces
find adversarial_corpora -name "*.json" -exec echo {} \; | wc -l
```

### Performance Thresholds

- **§PERF_THRESHOLD**: `Exit code 0 from audit_greenlight.py` (canonical: RUN_TO_GREEN.md §Step 6: Run Green-Light Audit)

### Safety Nets Count

- **§COUNT_Safety Nets**: Enhanced grep with false-positive filtering
  ```bash
  bash tools/verify_5_guards.sh | grep -c 'VERIFIED'
  ```

### Git Macros

- **§GIT_CHECKPOINT(msg)**: `git add -A && git commit -m "<msg>"`
- **§GIT_TAG(name)**: `git tag <name>`
- **§GIT_ROLLBACK**: `git reset --hard HEAD~1`

---

## Canonical Schema Definitions

### {{OUTPUT_SCHEMA_NAME}} Schema (v{{SCHEMA_VERSION}})

```typescript
{
  {{SCHEMA_FIELD_1}}: {{SCHEMA_TYPE_1}},
  {{SCHEMA_FIELD_2}}: {{SCHEMA_TYPE_2}},
  {{SCHEMA_FIELD_3}}: {
    {{NESTED_FIELD_1}}: {{NESTED_TYPE_1}},
    {{NESTED_FIELD_2}}: {{NESTED_TYPE_2}}
  }
}
```

### Phase Completion Artifact Schema (v{{SCHEMA_VERSION}})

See "Phase Unlock Mechanism" section above.

### Evidence Block Schema (v{{SCHEMA_VERSION}})

```json
{
  "evidence_id": "{{EVIDENCE_ID_EXAMPLE}}",
  "phase": 1,
  "file": "{{FILE_PATH_EXAMPLE}}",
  "lines": "{{LINE_RANGE_EXAMPLE}}",
  "description": "{{DESCRIPTION_EXAMPLE}}",
  "code_snippet": "{{SNIPPET_EXAMPLE}}",
  "sha256": "{{HASH_EXAMPLE}}",
  "timestamp": "{{TIMESTAMP_EXAMPLE}}"
}
```

---

## How to Use This Document

1. **Work sequentially** - Complete tasks in order within each phase
2. **Check off tasks** - Mark `[ ]` as `[x]` when complete
3. **Test continuously** - Run behavioral tests after every code change (§TEST_FAST or §TEST_FULL)
4. **Git checkpoints** - Use §GIT_CHECKPOINT(msg) before and after each task
5. **Document issues** - Note problems in `docs/CENTRAL_BACKLOG_README.md`
6. **Track time** - Record actual vs. estimated time
7. **Verify phase unlocks** - Check `.phase-1.complete.json` exists before starting Phase {{NEXT_PHASE}}

---

## Core Principle: YAGNI (You Aren't Gonna Need It)

**Rule**: Build only what has explicit metric triggers or P0 security requirement

### Testing Strategy

**Fast Iteration Loop** (during development):
```bash
# 1. Make small change to code
# 2. Quick test (~~2 minutes)
bash tools/run_5_tests.sh

# 3. If pass → continue to next change
# 4. If fail → revert immediately, debug, retry
```

**Full Validation** (before commit):
```bash
# Full behavioral (§CORPUS_COUNT files, ~~5 minutes)
.venv/bin/python -m pytest tests/ -v

# Performance check
python tools/audit_greenlight.py --report /tmp/audit.json

# CI gates
G1 → G2 → G3 → G4 → G5 (sequential execution required)
```

### When Tests Fail

1. **Immediate action**: `git status` to see what changed
2. **Revert**: `git restore <file>` or `git reset --hard HEAD`
3. **Debug**: Identify the specific line that broke test
4. **Smaller change**: Make more granular modification
5. **Retest**: Verify fix works
6. **Document**: Note the issue in `docs/CENTRAL_BACKLOG_README.md`

---

## Quick Reference Commands

```bash
# Fast subset test ({{SUBSET_NAME}} only)
bash tools/run_5_tests.sh           # ~~2 minutes, 5 files

# Full behavioral test
.venv/bin/python -m pytest tests/ -v

# All CI gates (G1→G5 sequential, explicit order)
bash tools/verify_5_guards.sh && .venv/bin/python -m pytest tests/ -v && python tools/audit_greenlight.py --report /tmp/audit.json

# Git checkpoint
git add -A && git commit -m "{{CHECKPOINT_MESSAGE}}"

# Rollback last commit
git reset --hard HEAD~1

# Check current Safety Nets usage
bash tools/verify_5_guards.sh | grep -c 'VERIFIED' | wc -l

# Progress tracking
{{PROGRESS_COMMAND}}

# Preflight check before phase
{{PREFLIGHT_COMMAND}} <phase_number>
```

---

## Phase 0: Prerequisites & Setup

**Goal**: Verify environment, tools, and baseline configuration
**Time**: 15 minutes
**Status**: ⏳ Not started

### Task 0.0: Verify Python Environment

**Time**: 5 minutes
**Files**: `.venv/bin/python, pyproject.toml`
**Test**: .venv/bin/python --version

**Steps**:
- [ ] Read `PLAN_CLOSING_IMPLEMENTATION.md` for context and principles
**⚠️ All steps must be checked! Do not skip any step.**

- [ ] {{STEP_1}}
- [ ] {{STEP_2}}
- [ ] {{STEP_3}}

**Acceptance Criteria**:
- [ ] All 5 safety nets verified and functional (S1, S2, R1, R2, C1)
- [ ] All 4 behavioral tests passing with 100% pass rate (14/14 sub-tests)
- [ ] Green-light audit exits with code 0 and 48-hour clean canary run

**Status**: ⏳ Not started

---

### Task 0.1: Verify Tool Inventory

**Time**: 5 minutes
**Files**: `tools/*.py, tools/*.sh`
**Test**: ls -la tools/
**References**: tools/README.md

**Steps**:
- [ ] Read `PLAN_CLOSING_IMPLEMENTATION.md` for context and principles
**⚠️ All steps must be checked! Do not skip any step.**

- [ ] {{STEP_1}}
  - [ ] {{SUBSTEP_1}}
  - [ ] {{SUBSTEP_2}}
- [ ] {{STEP_2}}
- [ ] {{STEP_3}}

**Acceptance Criteria**:
- [ ] All 5 safety nets verified and functional (S1, S2, R1, R2, C1)
- [ ] All 4 behavioral tests passing with 100% pass rate (14/14 sub-tests)
- [ ] Green-light audit exits with code 0 and 48-hour clean canary run

**Status**: ⏳ Not started

**Summary**:
- **safety_nets_count**: {{METRIC_1_VALUE}}
- **{{METRIC_2}}**: {{METRIC_2_VALUE}}
- **{{OUTPUT_FILE_1}}**: `{{OUTPUT_FILE_1_PATH}}`
- **{{OUTPUT_FILE_2}}**: `{{OUTPUT_FILE_2_PATH}}`

---

## Phase 1: {{PHASE_NAME}}

**Goal**: {{PHASE_GOAL}}
**Time**: {{PHASE_TIME}}
**Status**: ⏳ Not started
**Prerequisites**: Phase 0 complete (`.phase-0.complete.json` exists)

### Task {{TASK_NUM}}: {{TASK_NAME}}

**Time**: {{TASK_TIME}}
**Files**: `{{TASK_FILES}}`
**Test**: {{TASK_TEST}}
**References**: {{TASK_REFERENCES}}

**Steps**:
- [ ] {{STEP_1}}
- [ ] {{STEP_2}}
- [ ] {{STEP_3}}

**Acceptance Criteria**:
- [ ] All 5 safety nets verified and functional (S1, S2, R1, R2, C1)
- [ ] All 4 behavioral tests passing with 100% pass rate (14/14 sub-tests)
- [ ] Green-light audit exits with code 0 and 48-hour clean canary run

**Status**: ⏳ Not started

---

## Appendix A: Rollback Procedures

### A.1: Single Test Failure (Targeted Revert)

```bash
# 1. Check what changed
git status
git diff

# 2. Identify the problematic change
# Review the diff to find the specific issue

# 3. Revert specific file
git restore {{FILE_PATH}}

# 4. Quick retest
bash tools/run_5_tests.sh

# 5. If still fails, full revert
git reset --hard HEAD
.venv/bin/python -m pytest tests/ -v
```

---

### A.2: Multiple Test Failures (Full Revert)

```bash
# 1. Immediate rollback to last checkpoint
git reset --hard HEAD~1

# 2. Verify behavioral restored
.venv/bin/python -m pytest tests/ -v

# 3. If behavioral still broken, rollback to phase tag
git reset --hard phase-1-complete

# 4. Verify phase unlock artifact matches
cat .phase-1.complete.json
git log -1 --format=%H

# 5. Full validation
bash tools/verify_5_guards.sh && .venv/bin/python -m pytest tests/ -v && python tools/audit_greenlight.py --report /tmp/audit.json
```

---

### A.3: Performance Regression (Profile & Decide)

```bash
# 1. Profile the slow code
{{PROFILE_COMMAND}}

# 2. Analyze top 5 hotspots
# Review profiler output

# 3. Decision: Can we fix in <30 minutes>?
# YES → Fix the hotspot, retest
# NO  → Rollback and rethink approach

# 4. If rollback needed
git reset --hard HEAD~1
python tools/capture_baseline_metrics.py --auto --out /tmp/metrics.json
```

---

### A.4: CI Gate Failure (Diagnose & Fix)

```bash
# 1. Run gates individually to isolate failure
bash tools/verify_5_guards.sh
.venv/bin/python -m pytest tests/test_*.py -v
python tools/audit_greenlight.py --report /tmp/audit.json

# 2. Common failures and fixes:

# G1 (5 Safety Nets Verification) fails → Check .github/workflows/, tools/, and prometheus/ directories for missing files

# G2 (Behavioral Tests) fails → Review test output, fix mock issues, ensure test environment is clean

# G3 (Green-Light Audit) fails → Review audit report JSON, fix P0 failures (exit 5/6), ensure GITHUB_TOKEN set

# 3. If can't fix in 60 minutes → Rollback
git reset --hard HEAD~1
```

---

### A.5: {{CUSTOM_FAILURE_TYPE}} ({{CUSTOM_FAILURE_ACTION}})

```bash
# 1. {{STEP_1}}
{{COMMAND_1}}

# 2. {{STEP_2}}
{{COMMAND_2}}

# 3. {{STEP_3}}
# {{STEP_3_DESCRIPTION}}

# 4. {{STEP_4}}
{{COMMAND_4}}

# 5. If complex issue → Rollback and document
git reset --hard HEAD~1
echo "{{ISSUE_DESCRIPTION}}" >> docs/CENTRAL_BACKLOG_README.md
```

---

### A.6: Emergency: Lost All Changes

```bash
# 1. Check reflog (git keeps deleted commits for ~90 days)
git reflog

# 2. Find the last good commit
git reflog | grep "phase"

# 3. Restore to that commit
git reset --hard {{COMMIT_HASH}}

# 4. Verify phase unlock artifacts
ls -la .phase-*.complete.json

# 5. Full validation
bash tools/verify_5_guards.sh && .venv/bin/python -m pytest tests/ -v && python tools/audit_greenlight.py --report /tmp/audit.json
```

---

## Appendix B: Phase Completion Template

### B.1: Phase Completion Checklist

**Run these commands in order**:

```bash
# Full behavioral test (corpus count computed dynamically)
.venv/bin/python -m pytest tests/ -v

# Get dynamic corpus count for verification
ls -1 adversarial_corpora/*.json | wc -l

# Performance validation
python tools/capture_baseline_metrics.py --auto --out /tmp/metrics.json
# Verify: Exit code 0 from audit_greenlight.py

# All CI gates
bash tools/verify_5_guards.sh && .venv/bin/python -m pytest tests/ -v && python tools/audit_greenlight.py --report /tmp/audit.json
# Verify: All gates exit 0

# Count Safety Nets usage
{{METRIC_COUNT_BEFORE}}={{METRIC_VALUE_BEFORE}}
{{METRIC_COUNT_AFTER}}={{METRIC_VALUE_AFTER}}

# Use §COUNT_Safety Nets pattern for accurate counting
bash tools/verify_5_guards.sh | grep -c 'VERIFIED'

# Verify: $Safety Nets_AFTER <= $Safety Nets_BEFORE (or equal if Phase {{SPECIAL_PHASE}})
```

**Create phase unlock artifact**:

```python
# python tools/generate_decision_artifact.py
from pathlib import Path
import json
import subprocess
from datetime import datetime

# Load previous phase artifact for comparison
prev_artifact = json.loads(Path(".phase-0.complete.json").read_text())

# Count dynamic values
corpus_count = {{CORPUS_COUNT_EXPRESSION}}

# Use §COUNT_Safety Nets pattern for accurate Safety Nets counting
Safety Nets_count = {{METRIC_COUNT_EXPRESSION}}

# Get performance deltas from {{PERF_GATE_SCRIPT}} output
# Parse JSON from last line only (ignores warnings/logs)
perf_result = subprocess.run(
    [{{PERF_COMMAND}}],
    capture_output=True,
    text=True,
    timeout=30
)
perf_data = json.loads(perf_result.stdout.strip().split('\n')[-1])

# Create artifact
artifact = {
    "schema_version": "1.0",
    "min_schema_version": "1.0",
    "phase": 1,
    "phase_name": "{{PHASE_NAME}}",
    "baseline_pass_count": corpus_count,
    "ci_gates_passed": ["G1", "G2", "G3", "G4", "G5"],
    "Safety Nets_before": prev_artifact["Safety Nets_after"],
    "Safety Nets_after": Safety Nets_count,
    "performance_delta_median": perf_data["delta_median"],
    "performance_delta_p95": perf_data["delta_p95"],
    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "completion_date": datetime.utcnow().isoformat() + "Z",
    "evidence_blocks": []  # Populated separately
}

# Write atomically
from tools.atomic_write import atomic_write_text
atomic_write_text(Path(".phase-1.complete.json"), json.dumps(artifact, indent=2))
print(f"✓ Phase 1 unlock artifact created")
```

**Create completion report**:

```markdown
# Phase 1 Completion Report

**Date**: 2025-10-18
**Phase**: 1 - {{PHASE_NAME}}
**Status**: ✅ Complete

## Summary

{{SUMMARY_TEXT}}

## Changes Made

### Code Changes

{{CODE_CHANGES}}

### Methods Added

{{METHODS_ADDED}}

### Methods Removed

{{METHODS_REMOVED}}

## Validation Results

### behavioral Tests

- **Pass count**: {{PASS_COUNT}}/{{TOTAL_COUNT}}
- **Duration**: {{DURATION}}

### Performance

- **Median delta**: {{MEDIAN_DELTA}}
- **P95 delta**: {{P95_DELTA}}
- **Threshold**: {{PERF_THRESHOLD}}

### CI Gates

- **G1 (5 Safety Nets Verification)**: ✅ Pass
- **G2 (Behavioral Tests)**: ✅ Pass
- **G3 (Green-Light Audit)**: ✅ Pass
- **G4 (HMAC Policy Check)**: ✅ Pass
- **G5 (Telemetry Infrastructure)**: ✅ Pass

### Safety Nets Count

- **Before**: {{BEFORE_COUNT}}
- **After**: {{AFTER_COUNT}}
- **Delta**: {{DELTA}}

## Evidence Blocks

{{EVIDENCE_LIST}}

## Issues Encountered

{{ISSUES}}

### Issue 1: {{ISSUE_TITLE}}

**Description**: {{ISSUE_DESCRIPTION}}

**Resolution**: {{ISSUE_RESOLUTION}}

## Time Tracking

- **Estimated**: {{ESTIMATED_TIME}}
- **Actual**: {{ACTUAL_TIME}}
- **Variance**: {{VARIANCE}}

## Deviations from Specification

{{DEVIATIONS}}

## Next Steps

{{NEXT_STEPS}}
```

**Create evidence blocks**:

```python
# Use the centralized evidence utility (with portalocker locking)
import json
import subprocess

evidence_blocks = [
    {
        "evidence_id": "{{EVIDENCE_ID_1}}",
        "phase": 1,
        "file": "{{FILE_1}}",
        "lines": "{{LINES_1}}",
        "description": "{{DESCRIPTION_1}}"
    },
    {
        "evidence_id": "{{EVIDENCE_ID_2}}",
        "phase": 1,
        "file": "{{FILE_2}}",
        "lines": "{{LINES_2}}",
        "description": "{{DESCRIPTION_2}}"
    }
]

for block in evidence_blocks:
    result = subprocess.run(
        ["python3", "tools/create_evidence_block.py"],
        input=json.dumps(block),
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        print(f"Failed to create evidence block {block['evidence_id']}: {result.stderr}")
    else:
        print(f"✓ Created {block['evidence_id']}")
```

Helper function for phase completion:

```python
def count_evidence_blocks(phase: int) -> int:
    """Count evidence blocks created for a specific phase."""
    from pathlib import Path
    import json

    evidence_file = Path("evidence_blocks.jsonl")
    if not evidence_file.exists():
        return 0

    count = 0
    for line in evidence_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            block = json.loads(line)
            if block.get("phase") == phase:
                count += 1

    return count
```

#### Step 6: Git Checkpoint and Tag

```bash
# Commit all changes
§GIT_CHECKPOINT("Phase 1 complete - all validations pass")

# Create phase tag
§GIT_TAG(phase-1-complete)

# Verify tag created
git tag | grep phase-1-complete
```

---

### B.2: Phase Completion Acceptance Criteria

**Before marking phase complete, verify ALL of these**:

- [ ] All behavioral tests pass (§CORPUS_COUNT/§CORPUS_COUNT)
- [ ] Performance within budget ({{PERF_THRESHOLD}})
- [ ] All CI gates pass (G1-G5)
- [ ] Safety Nets count verified (5/5 present)
- [ ] Phase unlock artifact created and valid
- [ ] Completion report created with all sections filled
- [ ] tools/README.md updated
- [ ] Evidence blocks created (if code changes significant)
- [ ] Git checkpoint created
- [ ] Git tag created (`phase-1-complete`)
- [ ] No leftover fallback artifacts in workspace

**If ANY criterion fails**: Do NOT mark phase complete. Fix the issue or rollback per Appendix A.

---

## Appendix C: Progress Tracking

### Completed Tasks

Track here or in separate `PROGRESS_TRACKING.md` file:

**Phase 0**:
- [ ] Task 0.0: Verify Python Environment
- [ ] Task 0.1: Verify Tool Inventory
- [ ] Task 0.2: {{TASK_0_2_NAME}}

**Phase 1**:
- [ ] Task {{TASK_NUM_1}}: {{TASK_NAME_1}}
- [ ] Task {{TASK_NUM_2}}: {{TASK_NAME_2}}
- [ ] Task {{TASK_NUM_3}}: {{TASK_NAME_3}}

### Time Tracking

| Phase | Task | Estimated | Actual | Variance | Notes |
|-------|------|-----------|--------|----------|-------|
| 0     | 0.0  | {{EST_1}} | -      | -        | -     |
| 0     | 0.1  | {{EST_2}} | -      | -        | -     |
| ...   | ...  | ...       | ...    | ...      | ...   |

**Total Time**:
- **Estimated**: {{TOTAL_ESTIMATED}}
- **Actual**: [TBD]
- **Variance**: [TBD]

---

**Last Updated**: 2025-10-18
**Status**: {{CURRENT_STATUS}}
**Next Task**: {{NEXT_TASK}}
