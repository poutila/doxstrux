# AI Task List Linter v1.5

Deterministic linter for AI Task Lists (Spec v1.3).

## What's Fixed in v1.5

**All four gaps that allowed "lint passes, reality fails" are now closed:**

| Gap | Issue | Fix |
|-----|-------|-----|
| **A** | STOP labels optional | Labels `# Test run output:` and `# Symbol/precondition check output:` now ALWAYS required |
| **B** | Headers-only evidence passes | Captured headers (`# cmd:`, `# exit:`) no longer count as "evidence content" |
| **C** | UV false positives on output | Forbidden patterns only checked on `$` command lines, not pasted output |
| **D** | Phase Unlock Artifact weak | Must have fenced code block with specific artifact file (`.phase-N.complete.json`) |

## Run

```bash
# Standard lint
uv run python ai_task_list_linter_v1_5.py PROJECT_TASKS.md

# With captured evidence header enforcement (opt-in)
uv run python ai_task_list_linter_v1_5.py --require-captured-evidence PROJECT_TASKS.md

# JSON output
uv run python ai_task_list_linter_v1_5.py --json PROJECT_TASKS.md
```

Exit codes: 0 = pass, 1 = lint violations, 2 = usage/internal error

## STOP Evidence Format (Required)

Every non-Phase-0 task STOP block must have BOTH labeled sections with real output:

```markdown
**Evidence** (paste output):
```
# Test run output:
===== test session starts =====
collected 5 items
tests/test_main.py::test_something PASSED
===== 1 passed in 0.03s =====

# Symbol/precondition check output:
src/main.py:10:def main():
```
```

**Note**: `# cmd:` and `# exit:` headers do NOT satisfy the "real output" requirement.

## Phase Unlock Artifact Format (Required)

Must include a fenced code block with specific artifact file:

```markdown
## Phase Unlock Artifact

```bash
cat > .phase-0.complete.json << EOF
{
  "phase": 0,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "result": "PASS"
}
EOF
```
```

## Rules Summary

| Rule | Description | v1.5 Change |
|------|-------------|-------------|
| R-ATL-023 | STOP evidence labels + real output | **STRENGTHENED** |
| R-ATL-024 | Captured evidence headers | Opt-in |
| R-ATL-050 | Phase Unlock Artifact | **STRENGTHENED** |
| R-ATL-071 | Runner prefix on $ lines | — |
| R-ATL-072 | UV forbidden patterns | **FIXED** (no false positives) |

## Test Results

```
✅ Template passes
✅ Valid document passes  
✅ Gap A: STOP without labels → FAILS (R-ATL-023)
✅ Gap B: Headers-only evidence → FAILS (R-ATL-023)
✅ Gap C: UV "pip install" in output → PASSES (no false positive)
✅ Gap D: Prose-only Phase Unlock → FAILS (R-ATL-050)
```

## Migration from v1.4

1. **STOP evidence blocks** must now include both labels with real output:
   - `# Test run output:` with actual test output below
   - `# Symbol/precondition check output:` with actual rg/grep output below

2. **Phase Unlock Artifact** must include:
   - A fenced code block (not just prose)
   - Specific artifact file (`.phase-0.complete.json`, not `.phase-N.complete.json`)

3. **No changes needed** for UV forbidden patterns (fix is backward compatible)

## Design Philosophy

v1.5 closes all known loopholes where a document could be structurally valid but semantically empty. The linter now enforces that evidence sections contain **real output**, not just metadata or labels.

This eliminates the primary source of iteration loops: "did you run tests?" / "where is the proof?"
