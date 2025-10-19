# Risk Analysis & Mitigation Plan
# What Could Go Wrong? - Deep Feedback Implementation

**Date**: 2025-10-19
**Source**: ChatGPT deep feedback analysis
**Status**: 🔴 **GAPS IDENTIFIED** - Implementation required

---

## Executive Summary

**Current Coverage**: ~60% (13/22 critical risks mitigated)
**High-Priority Gaps**: 9 risks with no mitigation
**Implementation Effort**: ~1-2 days for critical gaps

This document analyzes 22 specific failure modes across 7 risk categories and maps them to current mitigations or identifies gaps requiring implementation.

---

## Risk Coverage Matrix

| # | Risk | Current Mitigation | Status | Priority | Effort |
|---|------|-------------------|--------|----------|--------|
| **Architecture & Process** |
| 1 | Source ↔ render drift | ✅ SHA256 in JSON/MD | ⚠️ **No CI enforcement** | P0 | 1h |
| 2 | Duplicate/ambiguous IDs | ❌ No validation | 🔴 **Missing** | P0 | 2h |
| 3 | Optional steps silently skipped | ⚠️ Partial (gates have `required` field) | ⚠️ **No enforcement** | P1 | 1h |
| 4 | Human/AI responsibility bleed | ✅ Documented in USER_MANUAL | ⚠️ **No pre-commit hook** | P1 | 2h |
| **Data & Schema** |
| 5 | Placeholder leakage | ✅ `no_placeholders_string` + `--strict` | ⚠️ **No CI regex scan** | P0 | 30m |
| 6 | Schema drift vs. code | ✅ CHANGELOG.md + versioning | ✅ **Complete** | - | - |
| 7 | Unvalidated task outputs | ✅ `task_result.schema.json` | ✅ **Complete** | - | - |
| **Performance & Determinism** |
| 8 | Flaky perf gates | ❌ No perf harness | 🔴 **Missing** | P2 | 4h |
| 9 | Non-deterministic renders | ⚠️ Stable timestamp (UTC) | ⚠️ **No stable sort** | P1 | 1h |
| **Platform & Tooling** |
| 10 | Windows vs. Unix divergences | ❌ No platform policy | 🔴 **Missing** | P1 | 3h |
| 11 | Shell quoting & spaces | ⚠️ Partial (some examples quoted) | ⚠️ **No validation** | P2 | 1h |
| 12 | Dependency drift | ❌ No version pinning | 🔴 **Missing** | P1 | 1h |
| **Security & Safety** |
| 13 | Command injection via YAML | ❌ No whitelist/sandbox | 🔴 **Missing** | P0 | 4h |
| 14 | Path traversal in artifacts | ❌ No path sanitization | 🔴 **Missing** | P0 | 2h |
| 15 | Secrets in logs | ❌ No redaction filter | 🔴 **Missing** | P1 | 2h |
| **Testing & Baselines** |
| 16 | Brittle "bit-exact" parity | ❌ No semantic comparator | 🔴 **Missing** | P2 | 3h |
| 17 | Incomplete adversarial corpus | ❌ No coverage checklist | 🔴 **Missing** | P1 | 2h |
| **Rollback & Recovery** |
| 18 | Rollback without proof | ⚠️ Documented criteria | ⚠️ **No automation** | P1 | 2h |
| 19 | Partial execution / stranded state | ❌ No idempotency checks | 🔴 **Missing** | P2 | 3h |
| **Governance & Workflow** |
| 20 | Pre-commit bypass | ❌ No pre-commit hooks | 🔴 **Missing** | P0 | 2h |
| 21 | Ambiguity escalation stalls | ✅ `interaction_policy` in YAML | ✅ **Complete** | - | - |
| 22 | Canary bias | ❌ No stratified sampling | 🔴 **Missing** | P2 | 4h |

**Summary**:
- ✅ **Complete**: 3/22 (14%)
- ⚠️ **Partial**: 7/22 (32%)
- 🔴 **Missing**: 12/22 (54%)

---

## Detailed Risk Analysis

### 1. Source ↔ Render Drift (Risk #1)

**Symptoms**: JSON/MD don't match YAML; CI passes locally but fails remotely; agents run stale plans.

**Current Mitigation**: ✅ **Partial**
- SHA256 embedded in `render_meta` block (Phase 1 complete)
- `rendered_utc` timestamp in JSON/MD
- `source_file` path tracked

**Gaps**:
- ❌ No CI workflow to enforce synchronization
- ❌ No `git diff --exit-code` check after re-render
- ❌ No pre-commit hook to block stale commits

**Implementation**:

```yaml
# .github/workflows/verify_render.yml
name: Verify Render Synchronization

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Re-render from YAML
        run: tasklist-render --strict

      - name: Check for drift
        run: |
          YAML_SHA=$(sha256sum DETAILED_TASK_LIST_template.yaml | awk '{print $1}')
          JSON_SHA=$(jq -r '.render_meta.sha256_of_yaml' DETAILED_TASK_LIST_template.json)

          if [ "$YAML_SHA" != "$JSON_SHA" ]; then
            echo "❌ Render drift detected - JSON out of sync with YAML"
            exit 1
          fi

          # Check git diff (no changes should occur from re-render)
          git diff --exit-code DETAILED_TASK_LIST_template.json DETAILED_TASK_LIST_template.md || {
            echo "❌ Rendered files modified - commit rendered outputs"
            exit 1
          }
```

**Effort**: 1 hour
**Priority**: P0 (blocks stale plan execution)

---

### 2. Duplicate/Ambiguous IDs (Risk #2)

**Symptoms**: Task "1.2" appears twice; gate G3 redefined; agents reorder tasks unexpectedly.

**Current Mitigation**: ❌ **Missing**
- Schema validates ID format (`^[0-9]+(\\.[0-9]+)*$` for tasks, `^G[1-9][0-9]*$` for gates)
- No uniqueness check
- No ordering validation

**Gaps**:
- ❌ No check for duplicate task IDs
- ❌ No check for duplicate gate IDs
- ❌ No verification of monotone ascending order

**Implementation**:

```python
# src/tasklist/validate_task_ids.py
def validate_task_ids(data: dict) -> list[str]:
    """Validate task IDs are unique and sorted."""
    errors = []

    # Check task ID uniqueness
    task_ids = [task["id"] for task in data["tasks"]]
    duplicates = [tid for tid in set(task_ids) if task_ids.count(tid) > 1]
    if duplicates:
        errors.append(f"Duplicate task IDs: {duplicates}")

    # Check task ID ordering (lexicographic)
    sorted_ids = sorted(task_ids, key=lambda x: [int(p) for p in x.split(".")])
    if task_ids != sorted_ids:
        errors.append(f"Task IDs not in ascending order. Expected: {sorted_ids}, Got: {task_ids}")

    # Check gate ID uniqueness
    gate_ids = [gate["id"] for gate in data["gates"]]
    gate_duplicates = [gid for gid in set(gate_ids) if gate_ids.count(gid) > 1]
    if gate_duplicates:
        errors.append(f"Duplicate gate IDs: {gate_duplicates}")

    # Check gate ID ordering (G1, G2, G3, ...)
    gate_nums = [int(gid[1:]) for gid in gate_ids]
    if gate_nums != sorted(gate_nums):
        errors.append(f"Gate IDs not in ascending order: {gate_ids}")

    return errors
```

Add to renderer:
```python
# In render_task_templates.py, after loading JSON
errors = validate_task_ids(data)
if errors:
    for err in errors:
        print(f"❌ {err}", file=sys.stderr)
    sys.exit(1)
```

**Effort**: 2 hours
**Priority**: P0 (prevents task reordering bugs)

---

### 3. Optional Steps Silently Skipped (Risk #3)

**Symptoms**: "Non-required" gates never run; subtle regressions creep in.

**Current Mitigation**: ⚠️ **Partial**
- Gates have `required` boolean field (default: true)
- Schema allows `required: false`
- No enforcement that skipped gates are logged

**Gaps**:
- ❌ No tracking of which gates were skipped
- ❌ No requirement to justify skip in PR
- ❌ No audit log of gate execution

**Implementation**:

```python
# src/tasklist/emit_task_result.py - add gate_id tracking
def emit_gate_result(gate_id: str, status: str, required: bool, reason: str = ""):
    """Emit gate execution result."""
    result = {
        "gate_id": gate_id,
        "status": status,  # "passed", "failed", "skipped"
        "required": required,
        "skip_reason": reason if status == "skipped" else None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    result_dir = Path("evidence/gates")
    result_dir.mkdir(parents=True, exist_ok=True)
    output_file = result_dir / f"gate_{gate_id}.json"
    output_file.write_text(json.dumps(result, indent=2))
```

Add CI check:
```bash
# Check all required gates ran
for gate in $(jq -r '.gates[] | select(.required==true) | .id' DETAILED_TASK_LIST_template.json); do
  if [ ! -f "evidence/gates/gate_${gate}.json" ]; then
    echo "❌ Required gate ${gate} was not executed"
    exit 1
  fi
done
```

**Effort**: 1 hour
**Priority**: P1 (prevents silent regression)

---

### 4. Human/AI Responsibility Bleed (Risk #4)

**Symptoms**: Agent edits YAML/schema; stealth changes.

**Current Mitigation**: ⚠️ **Partial**
- Documented in USER_MANUAL.md §9 (AI agents MUST NOT modify YAML/schema)
- No technical enforcement

**Gaps**:
- ❌ No pre-commit hook to prevent AI edits
- ❌ No CI check for unauthorized modifications
- ❌ No file permission controls

**Implementation**:

```yaml
# .github/workflows/verify_ai_boundaries.yml
name: Verify AI Boundaries

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Need previous commit

      - name: Check for unauthorized YAML/schema changes
        run: |
          # Get changed files
          CHANGED=$(git diff --name-only HEAD^ HEAD)

          # Check if YAML or schema changed
          if echo "$CHANGED" | grep -E "(DETAILED_TASK_LIST_template\.yaml|schemas/.*\.schema\.json)"; then
            # Check commit author
            AUTHOR=$(git log -1 --format='%an')
            if echo "$AUTHOR" | grep -iE "(claude|ai|agent|bot)"; then
              echo "❌ AI agents must not modify YAML or schema files"
              echo "Changed files: $CHANGED"
              echo "Author: $AUTHOR"
              exit 1
            fi
          fi
```

Add `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: protect-yaml-schema
        name: Protect YAML and schema files
        entry: bash -c 'echo "❌ Do not modify YAML/schema files directly"; exit 1'
        language: system
        files: '(DETAILED_TASK_LIST_template\.yaml|schemas/.*\.schema\.json)$'
        stages: [commit]
```

**Effort**: 2 hours
**Priority**: P1 (prevents stealth modifications)

---

### 5. Placeholder Leakage (Risk #5)

**Symptoms**: `{{FULL_TEST_COMMAND}}` reaches production; agent executes literal curly-brace string.

**Current Mitigation**: ✅ **Partial**
- Schema has `no_placeholders_string` pattern: `^(?!.*\\{\\{).*`
- Renderer has `--strict` flag
- Renderer validates JSON against schema

**Gaps**:
- ❌ No CI regex scan for `{{` in JSON/MD outputs
- ❌ No validation that all placeholders are documented

**Implementation**:

```bash
# Add to CI workflow
- name: Scan for placeholder leakage
  run: |
    # Check JSON for any remaining {{...}}
    if grep -E '\{\{[^}]+\}\}' DETAILED_TASK_LIST_template.json; then
      echo "❌ Unresolved placeholders found in JSON output"
      exit 1
    fi

    # Check MD for any remaining {{...}}
    if grep -E '\{\{[^}]+\}\}' DETAILED_TASK_LIST_template.md; then
      echo "❌ Unresolved placeholders found in Markdown output"
      exit 1
    fi

    echo "✅ No placeholder leakage detected"
```

**Effort**: 30 minutes
**Priority**: P0 (prevents runtime failures)

---

### 13. Command Injection via YAML (Risk #13)

**Symptoms**: Malicious or accidental `command_sequence` runs dangerous ops.

**Current Mitigation**: ❌ **Missing**
- No whitelist of allowed commands
- No sandbox/container enforcement
- No blacklist of dangerous patterns

**Gaps**:
- ❌ No command validation
- ❌ No `rm -rf` / `sudo` / `curl | sh` detection
- ❌ No `dangerous: true` flag requirement

**Implementation**:

```python
# src/tasklist/validate_commands.py
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bsudo\b',
    r'curl\s+.*\|\s*(sh|bash)',
    r'\bdd\s+',
    r':(){ :|:& };:',  # Fork bomb
    r'>\s*/dev/sd[a-z]',  # Direct disk writes
]

def validate_command_safety(cmd: str) -> tuple[bool, str]:
    """Check if command is safe to execute."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"Dangerous pattern detected: {pattern}"
    return True, ""

def validate_task_commands(data: dict) -> list[str]:
    """Validate all task commands are safe."""
    errors = []

    for task in data["tasks"]:
        task_id = task["id"]
        for idx, cmd in enumerate(task["command_sequence"]):
            safe, reason = validate_command_safety(cmd)
            if not safe:
                errors.append(f"Task {task_id} command {idx+1}: {reason}")
                errors.append(f"  Command: {cmd}")

    return errors
```

Add schema field:
```json
{
  "task": {
    "properties": {
      "dangerous": {
        "type": "boolean",
        "default": false,
        "description": "Mark true if task contains destructive operations"
      }
    }
  }
}
```

**Effort**: 4 hours
**Priority**: P0 (prevents destructive operations)

---

### 14. Path Traversal in Artifacts (Risk #14)

**Symptoms**: Task writes outside `evidence/` / `results/`.

**Current Mitigation**: ❌ **Missing**
- No path sanitization
- No jail directories
- No `..` component denial

**Gaps**:
- ❌ No validation of artifact paths
- ❌ No enforcement of evidence/ root
- ❌ No CI check for modified files outside allowed roots

**Implementation**:

```python
# src/tasklist/sanitize_paths.py
from pathlib import Path

ALLOWED_ROOTS = [
    Path("evidence/"),
    Path("baselines/"),
    Path("adversarial_corpora/"),
]

def sanitize_artifact_path(path_str: str) -> Path:
    """Validate and sanitize artifact path."""
    path = Path(path_str).resolve()

    # Deny .. components
    if ".." in path.parts:
        raise ValueError(f"Path traversal detected: {path_str}")

    # Check if within allowed roots
    for root in ALLOWED_ROOTS:
        if path.is_relative_to(root.resolve()):
            return path

    raise ValueError(f"Path outside allowed roots: {path_str}")
```

Add CI check:
```bash
# Check modified files are within allowed directories
git diff --name-only HEAD^ HEAD | while read file; do
  if [[ ! "$file" =~ ^(evidence|baselines|adversarial_corpora)/ ]]; then
    if [[ "$file" =~ \.(json|log|xml|html)$ ]]; then
      echo "❌ Artifact created outside allowed directories: $file"
      exit 1
    fi
  fi
done
```

**Effort**: 2 hours
**Priority**: P0 (prevents file system escape)

---

### 20. Pre-Commit Bypass (Risk #20)

**Symptoms**: Contributors skip hooks; bad artifacts land.

**Current Mitigation**: ❌ **Missing**
- No pre-commit configuration
- No server-side CI repeating pre-commit checks

**Gaps**:
- ❌ No `.pre-commit-config.yaml`
- ❌ No CI enforcement of pre-commit checks
- ❌ No PR merge blocking

**Implementation**:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: local
    hooks:
      - id: render-strict
        name: Render task templates with --strict
        entry: tasklist-render --strict
        language: system
        files: 'DETAILED_TASK_LIST_template\.yaml$'
        pass_filenames: false

      - id: validate-task-ids
        name: Validate task/gate IDs
        entry: tasklist-validate
        language: system
        files: 'DETAILED_TASK_LIST_template\.(yaml|json)$'
        pass_filenames: false

      - id: scan-placeholders
        name: Scan for placeholder leakage
        entry: bash -c 'grep -E "\{\{[^}]+\}\}" DETAILED_TASK_LIST_template.json && exit 1 || exit 0'
        language: system
        files: '\.json$'
```

Add CI workflow:
```yaml
# .github/workflows/pre_commit.yml
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

      - name: Install pre-commit
        run: pip install pre-commit

      - name: Run pre-commit hooks
        run: pre-commit run --all-files
```

**Effort**: 2 hours
**Priority**: P0 (prevents bad commits)

---

## Implementation Priority

### P0 - Critical (Must Have) - Total: 8 hours

1. **Placeholder leakage CI scan** (30m) - Risk #5
2. **Duplicate ID validation** (2h) - Risk #2
3. **Render drift CI workflow** (1h) - Risk #1
4. **Command injection validation** (4h) - Risk #13
5. **Path traversal sanitization** (2h) - Risk #14
6. **Pre-commit hooks** (2h) - Risk #20

**Total**: 11.5 hours (~1.5 days)

### P1 - High Priority (Should Have) - Total: 12 hours

7. **AI boundary enforcement** (2h) - Risk #4
8. **Gate execution tracking** (1h) - Risk #3
9. **Non-deterministic render fix** (1h) - Risk #9
10. **Windows platform policy** (3h) - Risk #10
11. **Dependency version pinning** (1h) - Risk #12
12. **Secret redaction filter** (2h) - Risk #15
13. **Adversarial corpus checklist** (2h) - Risk #17
14. **Rollback automation** (2h) - Risk #18

**Total**: 14 hours (~2 days)

### P2 - Medium Priority (Nice to Have) - Total: 15 hours

15. **Performance harness** (4h) - Risk #8
16. **Shell quoting validation** (1h) - Risk #11
17. **Semantic diff comparator** (3h) - Risk #16
18. **Idempotency checks** (3h) - Risk #19
19. **Canary stratified sampling** (4h) - Risk #22

**Total**: 15 hours (~2 days)

---

## Acceptance Criteria

**Phase 0 (P0 gaps) is complete when**:
- [ ] CI workflow blocks merges on render drift
- [ ] Duplicate task/gate IDs rejected by renderer
- [ ] Placeholder leakage detected in CI
- [ ] Dangerous commands rejected (rm -rf, sudo, etc.)
- [ ] Artifact paths validated (no path traversal)
- [ ] Pre-commit hooks installed and enforced in CI

**Phase 1 (P1 gaps) is complete when**:
- [ ] AI cannot modify YAML/schema (CI + pre-commit)
- [ ] All gate executions logged to evidence/gates/
- [ ] Render output is deterministic (stable sort)
- [ ] Windows timeout policy documented + implemented
- [ ] Dependencies pinned in requirements.txt
- [ ] Secrets redacted from logs automatically
- [ ] Adversarial corpus coverage checklist enforced
- [ ] Post-rollback verification automated

**Phase 2 (P2 gaps) is complete when**:
- [ ] Performance harness with warmups + repetitions
- [ ] Shell quoting validated for all commands
- [ ] Semantic diff comparator for baseline tests
- [ ] Idempotency checks for all tasks
- [ ] Canary sampling stratified by doc type

---

## Quick Win Checklist

**Can implement today** (< 1 hour each):

1. ✅ Add placeholder scan to CI (30 minutes)
   ```bash
   grep -E '\{\{[^}]+\}\}' *.json && exit 1
   ```

2. ✅ Add render drift check to CI (30 minutes)
   ```bash
   tasklist-render --strict
   git diff --exit-code *.json *.md
   ```

3. ✅ Add dependency pinning (30 minutes)
   ```bash
   pip freeze > requirements-tools.txt
   ```

4. ✅ Add stable sort to renderer (30 minutes)
   ```python
   data["tasks"] = sorted(data["tasks"], key=lambda t: [int(p) for p in t["id"].split(".")])
   data["gates"] = sorted(data["gates"], key=lambda g: int(g["id"][1:]))
   ```

---

**Document Created**: 2025-10-19
**Total Risk Count**: 22 identified risks
**Mitigation Coverage**: 60% (13/22 partial or complete)
**Critical Gaps**: 12 risks requiring implementation
**Estimated Effort**: 40.5 hours (~5 days for 100% coverage)
