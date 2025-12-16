<!--
  CANONICAL EXAMPLE: Instantiated Mode

  Lint-passing example for instantiated mode (real commands, real evidence).

  Purpose: Regression test for linter - this file MUST pass lint with --require-captured-evidence.
  Run: uv run python tools/ai_task_list_linter.py --require-captured-evidence canonical_examples/example_instantiated.md
-->
---
ai_task_list:
  schema_version: "0.0.8"
  mode: "instantiated"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# Example Instantiated Task List (Mode: instantiated)

Task ID N.M → TASK_N_M_PATHS

## Non-negotiable Invariants

## Placeholder Protocol

## Source of Truth Hierarchy

## Phase 0 — Baseline Reality

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | 2025-12-15 |
| Repo | example_repo |
| Branch | main |
| Commit | abcdef1234567890 |
| Runner | uv 0.4.0 |
| Runtime | Python 3.12.1 |

**Evidence**:
```bash
$ uv sync
# cmd: uv sync
# exit: 0
sync complete
$ git rev-parse --abbrev-ref HEAD
# cmd: git rev-parse --abbrev-ref HEAD
# exit: 0
main
```

**Baseline tests**:
```bash
$ uv run pytest -q
# cmd: uv run pytest -q
# exit: 0
5 passed in 0.42s
```

## Global Clean Table Scan
```bash
$ ! rg 'TODO|FIXME|XXX' src/
# cmd: ! rg 'TODO|FIXME|XXX' src/
# exit: 0
$ rg 'from \.\.' src/
$ rg 'import \*' src/
```

## STOP — Phase Gate
- [x] All Phase N tasks ✅ COMPLETE
- [x] Phase N tests pass
- [x] Global Clean Table scan passes (output pasted above)
- [x] `.phase-N.complete.json` exists
- [x] Drift ledger current

## Drift Ledger (append-only)
| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
|      |        |       |          |            |          |

## Phase Unlock Artifact
```bash
$ cat > .phase-1.complete.json << EOF
{
  "phase": 1,
  "completed_at": "2025-12-15T00:00:00Z",
  "commit": "abcdef1234567890"
}
EOF
$ if rg '\[\[PH:' .phase-1.complete.json; then exit 1; fi
```

## Prose Coverage Mapping
| Prose requirement | Source (file/section) | Implemented by Task(s) |
|-------------------|-----------------------|------------------------|
| Example requirement | example_spec.md#1 | 1.1 |
| Baseline capture | example_spec.md#2 | 1.2 |

### Task 1.1 — Initial wiring

TASK_1_1_PATHS=(
  "src/example_module.py"
)

**Status**: ✅ COMPLETE

**Preconditions (symbol check)**:
```bash
$ rg -n example src/example_module.py
```

### TDD Step 1 — Write test (RED)
```bash
$ uv run pytest -q tests/test_example_module.py::test_initial_wiring && exit 1 || true
```

### TDD Step 2 — Implement (minimal)
```bash
$ uv run python -c "print('implement wiring')"
```

### TDD Step 3 — Verify (GREEN)
```bash
$ uv run pytest -q tests/test_example_module.py::test_initial_wiring
```

### STOP — Clean Table
- [x] Stub/no-op would FAIL this test?
- [x] Asserts semantics, not just presence?
- [x] Has negative case for critical behavior?
- [x] Is NOT import-only/smoke/existence-only/exit-code-only?
- [x] Tests pass (not skipped)
- [x] Full suite passes
- [x] No placeholders remain
- [x] Paths exist
- [x] Drift ledger updated
**Evidence (paste output)**:
```bash
# Test run output:
# cmd: uv run pytest -q tests/test_example_module.py::test_initial_wiring
# exit: 0
1 passed
# Symbol/precondition check output:
# cmd: rg -n example src/example_module.py
# exit: 0
1:example content
```

### Task 1.2 — Baseline capture

TASK_1_2_PATHS=(
  "tests/test_baseline.py"
)

**Status**: ✅ COMPLETE

**Preconditions (symbol check)**:
```bash
$ rg -n baseline tests/test_baseline.py
```

### TDD Step 1 — Write test (RED)
```bash
$ uv run pytest -q tests/test_baseline.py::test_baseline && exit 1 || true
```

### TDD Step 2 — Implement (minimal)
```bash
$ uv run python -c "print('collect baseline')"
```

### TDD Step 3 — Verify (GREEN)
```bash
$ uv run pytest -q tests/test_baseline.py::test_baseline
```

### STOP — Clean Table
- [x] Stub/no-op would FAIL this test?
- [x] Asserts semantics, not just presence?
- [x] Has negative case for critical behavior?
- [x] Is NOT import-only/smoke/existence-only/exit-code-only?
- [x] Tests pass (not skipped)
- [x] Full suite passes
- [x] No placeholders remain
- [x] Paths exist
- [x] Drift ledger updated
**Evidence (paste output)**:
```bash
# Test run output:
# cmd: uv run pytest -q tests/test_baseline.py::test_baseline
# exit: 0
1 passed
# Symbol/precondition check output:
# cmd: rg -n baseline tests/test_baseline.py
# exit: 0
1:baseline content
```
