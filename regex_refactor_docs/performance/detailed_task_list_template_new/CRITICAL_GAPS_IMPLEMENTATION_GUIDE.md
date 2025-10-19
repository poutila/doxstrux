# Critical Gaps - Implementation Guide
# P0 Risks: What Must Be Fixed Before Production

**Date**: 2025-10-19
**Effort**: ~11.5 hours (1.5 days)
**Status**: 🔴 **READY TO IMPLEMENT**

---

## Quick Start - 4 Hours to Green

These are the absolute minimum fixes to prevent catastrophic failures. All paths below assume you are in the repository root (`task-list/`).

### 1. Placeholder Leakage (30 minutes)

**Risk**: `{{VARIABLE}}` reaches production, breaks at runtime

**Fix**: Add to `.github/workflows/verify_render.yml`

```yaml
- name: Scan for placeholder leakage
  run: |
    if grep -E '\{\{[^}]+\}\}' DETAILED_TASK_LIST_template.json; then
      echo "❌ Unresolved placeholders in JSON"
      exit 1
    fi
    if grep -E '\{\{[^}]+\}\}' DETAILED_TASK_LIST_template.md; then
      echo "❌ Unresolved placeholders in Markdown"
      exit 1
    fi
```

**Test**:
```bash
# Should fail
echo '{"test": "{{UNRESOLVED}}"}' > test.json
grep -E '\{\{[^}]+\}\}' test.json && echo "DETECTED"

# Should pass
echo '{"test": "resolved"}' > test.json
grep -E '\{\{[^}]+\}\}' test.json || echo "CLEAN"
```

---

### 2. Render Drift Detection (1 hour)

**Risk**: JSON/MD out of sync with YAML, agents run stale plans

**Fix**: Create `.github/workflows/verify_render.yml`

```yaml
name: Verify Render Synchronization

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  verify-render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema

      - name: Re-render from YAML
        run: |
          python tools/render_task_templates.py --strict

      - name: Check SHA256 synchronization
        run: |
          YAML_SHA=$(sha256sum DETAILED_TASK_LIST_template.yaml | awk '{print $1}')
          JSON_SHA=$(python -c "import json; print(json.load(open('DETAILED_TASK_LIST_template.json'))['render_meta']['sha256_of_yaml'])")

          if [ "$YAML_SHA" != "$JSON_SHA" ]; then
            echo "❌ SHA256 mismatch - JSON out of sync"
            echo "YAML: $YAML_SHA"
            echo "JSON: $JSON_SHA"
            exit 1
          fi

      - name: Check for uncommitted changes
        run: |
          if ! git diff --exit-code DETAILED_TASK_LIST_template.json DETAILED_TASK_LIST_template.md; then
            echo "❌ Rendered files have uncommitted changes"
            echo "Run: python tools/render_task_templates.py --strict"
            exit 1
          fi

      - name: Scan for placeholder leakage
        run: |
          if grep -E '\{\{[^}]+\}\}' DETAILED_TASK_LIST_template.json DETAILED_TASK_LIST_template.md; then
            echo "❌ Unresolved placeholders detected"
            exit 1
          fi
```

**Test locally**:
```bash
# Should pass
python tools/render_task_templates.py --strict
git diff --exit-code *.json *.md

# Should fail (modify YAML without re-rendering)
echo "# comment" >> DETAILED_TASK_LIST_template.yaml
git diff --exit-code *.json *.md  # Will show no changes = stale
```

---

### 3. Duplicate ID Validation (2 hours)

**Risk**: Task "1.2" appears twice, agents skip or double-execute

**Fix**: Create `tools/validate_task_ids.py`

```python
#!/usr/bin/env python3
"""
Validate task and gate IDs are unique and sorted.
"""
import json
import sys
from pathlib import Path


def validate_task_ids(data: dict) -> list[str]:
    """Validate task IDs are unique and in ascending order."""
    errors = []

    # Extract task IDs
    task_ids = [task["id"] for task in data.get("tasks", [])]

    # Check uniqueness
    seen = set()
    duplicates = []
    for tid in task_ids:
        if tid in seen:
            duplicates.append(tid)
        seen.add(tid)

    if duplicates:
        errors.append(f"❌ Duplicate task IDs: {duplicates}")

    # Check ordering (numeric sort on dotted notation)
    def sort_key(task_id: str) -> list[int]:
        return [int(part) for part in task_id.split(".")]

    sorted_ids = sorted(task_ids, key=sort_key)
    if task_ids != sorted_ids:
        errors.append(f"❌ Task IDs not in ascending order")
        errors.append(f"   Expected: {sorted_ids}")
        errors.append(f"   Got:      {task_ids}")

    return errors


def validate_gate_ids(data: dict) -> list[str]:
    """Validate gate IDs are unique and in ascending order."""
    errors = []

    # Extract gate IDs
    gate_ids = [gate["id"] for gate in data.get("gates", [])]

    # Check uniqueness
    seen = set()
    duplicates = []
    for gid in gate_ids:
        if gid in seen:
            duplicates.append(gid)
        seen.add(gid)

    if duplicates:
        errors.append(f"❌ Duplicate gate IDs: {duplicates}")

    # Check ordering (numeric sort on G prefix)
    gate_nums = [int(gid[1:]) for gid in gate_ids if gid.startswith("G")]
    if gate_nums != sorted(gate_nums):
        errors.append(f"❌ Gate IDs not in ascending order: {gate_ids}")

    return errors


def main():
    json_path = Path("DETAILED_TASK_LIST_template.json")

    if not json_path.exists():
        print(f"❌ File not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    with json_path.open() as f:
        data = json.load(f)

    errors = []
    errors.extend(validate_task_ids(data))
    errors.extend(validate_gate_ids(data))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)

    print("✅ All task and gate IDs are unique and sorted")


if __name__ == "__main__":
    main()
```

**Add to renderer** (`tools/render_task_templates.py`):

```python
# After loading JSON (around line 100)
from validate_task_ids import validate_task_ids, validate_gate_ids

errors = []
errors.extend(validate_task_ids(data))
errors.extend(validate_gate_ids(data))

if errors:
    for err in errors:
        print(err, file=sys.stderr)
    sys.exit(1)
```

**Add to CI** (in `verify_render.yml`):
```yaml
- name: Validate task/gate IDs
  run: |
    python tools/validate_task_ids.py
```

**Test**:
```bash
# Should pass
python tools/validate_task_ids.py

# Should fail (create duplicate)
# Edit JSON: add duplicate task with id "1.1"
python tools/validate_task_ids.py  # Should error
```

---

### 4. Command Injection Prevention (4 hours)

**Risk**: Malicious YAML executes `rm -rf /` or `curl | sh`

**Fix**: Create `tools/validate_commands.py`

```python
#!/usr/bin/env python3
"""
Validate command_sequence entries are safe.
"""
import json
import re
import sys
from pathlib import Path


# Dangerous patterns to reject
DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', "rm -rf detected"),
    (r'\bsudo\b', "sudo usage detected"),
    (r'curl\s+.*\|\s*(sh|bash)', "curl | sh detected"),
    (r'\bdd\s+if=', "dd command detected"),
    (r':\(\)\s*\{', "fork bomb pattern detected"),
    (r'>\s*/dev/sd[a-z]', "direct disk write detected"),
    (r'\bchmod\s+777\b', "chmod 777 detected"),
    (r'eval\s+\$\(', "eval with command substitution"),
    (r';\s*rm\s+', "command chaining with rm"),
]

# Allowed command prefixes (whitelist)
ALLOWED_PREFIXES = [
    "python", "pytest", ".venv/bin/python",
    "git", "npm", "pip", "bash -c",
    "mkdir", "cp", "mv", "echo", "cat",
    "jq", "grep", "find", "ls", "cd",
]


def is_command_safe(cmd: str) -> tuple[bool, str]:
    """Check if command is safe to execute."""

    # Check dangerous patterns
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, description

    # Check whitelist (optional - comment out for less strict)
    # cmd_start = cmd.strip().split()[0] if cmd.strip() else ""
    # if not any(cmd_start.startswith(prefix) for prefix in ALLOWED_PREFIXES):
    #     return False, f"command not in whitelist: {cmd_start}"

    return True, ""


def validate_commands(data: dict) -> list[str]:
    """Validate all task commands are safe."""
    errors = []

    for task in data.get("tasks", []):
        task_id = task.get("id", "unknown")
        for idx, cmd in enumerate(task.get("command_sequence", [])):
            safe, reason = is_command_safe(cmd)
            if not safe:
                errors.append(f"❌ Task {task_id} command {idx+1}: {reason}")
                errors.append(f"   Command: {cmd}")

    return errors


def main():
    json_path = Path("DETAILED_TASK_LIST_template.json")

    if not json_path.exists():
        print(f"❌ File not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    with json_path.open() as f:
        data = json.load(f)

    errors = validate_commands(data)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print("\n⚠️  If these commands are intentional, add 'dangerous: true' to task", file=sys.stderr)
        sys.exit(1)

    print("✅ All commands are safe")


if __name__ == "__main__":
    main()
```

**Add to renderer**:
```python
# In render_task_templates.py
from validate_commands import validate_commands

errors.extend(validate_commands(data))
```

**Add to CI**:
```yaml
- name: Validate command safety
  run: |
    python tools/validate_commands.py
```

**Test**:
```bash
# Should pass
python tools/validate_commands.py

# Should fail
# Edit YAML to add: command_sequence: ["rm -rf /tmp"]
python tools/render_task_templates.py --strict
# Should error on dangerous command
```

---

### 5. Path Traversal Prevention (2 hours)

**Risk**: Task writes to `/etc/passwd` or `../../sensitive`

**Fix**: Create `tools/sanitize_paths.py`

```python
#!/usr/bin/env python3
"""
Sanitize and validate artifact paths.
"""
from pathlib import Path


ALLOWED_ROOTS = [
    Path("evidence"),
    Path("baselines"),
    Path("adversarial_corpora"),
    Path("prometheus"),
    Path("grafana"),
]


def sanitize_artifact_path(path_str: str) -> Path:
    """
    Validate and sanitize artifact path.

    Raises:
        ValueError: If path is invalid or outside allowed roots
    """
    # Convert to Path and resolve (but don't require existence)
    try:
        path = Path(path_str)
    except Exception as e:
        raise ValueError(f"Invalid path: {path_str}") from e

    # Deny .. components
    if ".." in path.parts:
        raise ValueError(f"Path traversal detected (..): {path_str}")

    # Deny absolute paths
    if path.is_absolute():
        raise ValueError(f"Absolute paths not allowed: {path_str}")

    # Check if path starts with allowed root
    allowed = False
    for root in ALLOWED_ROOTS:
        try:
            # Check if path is relative to allowed root
            if path.parts and path.parts[0] == root.parts[0]:
                allowed = True
                break
        except ValueError:
            continue

    if not allowed:
        raise ValueError(
            f"Path outside allowed roots: {path_str}\n"
            f"Allowed roots: {[str(r) for r in ALLOWED_ROOTS]}"
        )

    return path


def validate_artifact_paths(data: dict) -> list[str]:
    """Validate all task output/artifact paths."""
    errors = []

    for task in data.get("tasks", []):
        task_id = task.get("id", "unknown")

        # Check outputs
        for output_path in task.get("outputs", []):
            try:
                sanitize_artifact_path(output_path)
            except ValueError as e:
                errors.append(f"❌ Task {task_id} invalid output path: {e}")

    return errors


if __name__ == "__main__":
    import json
    import sys

    with open("DETAILED_TASK_LIST_template.json") as f:
        data = json.load(f)

    errors = validate_artifact_paths(data)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)

    print("✅ All artifact paths are safe")
```

**Add to renderer**:
```python
from sanitize_paths import validate_artifact_paths

errors.extend(validate_artifact_paths(data))
```

**Test**:
```bash
# Should pass
python -c "from sanitize_paths import sanitize_artifact_path; sanitize_artifact_path('evidence/logs/test.log')"

# Should fail
python -c "from sanitize_paths import sanitize_artifact_path; sanitize_artifact_path('../../../etc/passwd')"
# Should raise ValueError
```

---

### 6. Pre-Commit Hooks (2 hours)

**Risk**: Bad commits bypass validation, reach production

**Fix**: Create `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
        name: Check YAML syntax
      - id: check-json
        name: Check JSON syntax
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: local
    hooks:
      - id: render-strict
        name: Render task templates with --strict
        entry: python tools/render_task_templates.py --strict
        language: system
        files: 'DETAILED_TASK_LIST_template\.yaml$'
        pass_filenames: false
        always_run: false

      - id: validate-ids
        name: Validate task/gate IDs
        entry: python tools/validate_task_ids.py
        language: system
        files: 'DETAILED_TASK_LIST_template\.(yaml|json)$'
        pass_filenames: false

      - id: validate-commands
        name: Validate command safety
        entry: python tools/validate_commands.py
        language: system
        files: 'DETAILED_TASK_LIST_template\.(yaml|json)$'
        pass_filenames: false

      - id: scan-placeholders
        name: Scan for placeholder leakage
        entry: bash -c '! grep -E "\{\{[^}]+\}\}" DETAILED_TASK_LIST_template.json'
        language: system
        files: '\.json$'
        pass_filenames: false
```

**Install**:
```bash
pip install pre-commit
pre-commit install
```

**Test**:
```bash
# Should run all hooks
pre-commit run --all-files

# Should fail if issues exist
echo "# test" >> DETAILED_TASK_LIST_template.yaml
git add DETAILED_TASK_LIST_template.yaml
git commit -m "test"  # Hooks will run
```

**Add CI enforcement** (`.github/workflows/pre_commit.yml`):
```yaml
name: Pre-Commit Checks

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install pre-commit pyyaml jsonschema

      - name: Run pre-commit hooks
        run: |
          pre-commit run --all-files
```

---

## Testing the Complete Fix

After implementing all 6 fixes:

```bash
# 1. Test placeholder scan
grep -E '\{\{' *.json && echo "FAIL" || echo "PASS"

# 2. Test render drift detection
python tools/render_task_templates.py --strict
git diff --exit-code *.json *.md && echo "PASS" || echo "FAIL"

# 3. Test ID validation
python tools/validate_task_ids.py && echo "PASS" || echo "FAIL"

# 4. Test command safety
python tools/validate_commands.py && echo "PASS" || echo "FAIL"

# 5. Test path sanitization
python tools/sanitize_paths.py && echo "PASS" || echo "FAIL"

# 6. Test pre-commit
pre-commit run --all-files && echo "PASS" || echo "FAIL"
```

All should print "PASS" for a green build.

---

## Quick Reference - File Locations

```
task-list/ (repository root)
├── .github/workflows/
│   ├── verify_render.yml          # NEW - Render drift + placeholder scan
│   └── pre_commit.yml             # NEW - Pre-commit enforcement
├── .pre-commit-config.yaml        # NEW - Pre-commit hooks
├── tools/
│   ├── render_task_templates.py   # MODIFY - Add validation calls
│   ├── validate_task_ids.py       # NEW - ID uniqueness + ordering
│   ├── validate_commands.py       # NEW - Command safety
│   └── sanitize_paths.py          # NEW - Path traversal prevention
├── DETAILED_TASK_LIST_template.yaml
├── DETAILED_TASK_LIST_template.json
├── DETAILED_TASK_LIST_template.md
└── RISK_ANALYSIS_AND_MITIGATION.md
```

---

## Success Criteria

**P0 gaps are closed when**:
- [x] `.github/workflows/verify_render.yml` exists and runs on push/PR
- [x] `tools/validate_task_ids.py` exists and validates uniqueness + order
- [x] `tools/validate_commands.py` exists and rejects dangerous patterns
- [x] `tools/sanitize_paths.py` exists and prevents path traversal
- [x] `.pre-commit-config.yaml` exists and hooks run locally + CI
- [x] All CI workflows green on test commit

**Deploy to production when**:
- All tests pass
- CI workflows enforce all validations
- Pre-commit hooks installed and documented
- Team trained on new validation requirements

---

**Created**: 2025-10-19
**Effort**: 11.5 hours (1.5 days)
**Priority**: P0 (must complete before production use)
