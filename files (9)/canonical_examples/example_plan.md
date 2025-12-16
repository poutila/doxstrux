<!--
  CANONICAL EXAMPLE: Plan Mode

  Lint-passing example for plan mode (real commands, evidence placeholders allowed).

  Purpose: Regression test for linter - this file MUST pass lint.
  Run: uv run python ai_task_list_linter_v1_9.py canonical_examples/example_plan.md
-->
---
ai_task_list:
  schema_version: "1.7"
  mode: "plan"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# Example Plan Task List (Mode: plan)

Task ID N.M → TASK_N_M_PATHS

## Non-negotiable Invariants

## Placeholder Protocol

## Source of Truth Hierarchy

## Phase 0 — Baseline Reality
### Task 1.1 — Initial wiring

TASK_1_1_PATHS=(
  "src/example_module.py"
)

**Status**: 📋 PLANNED

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
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated
**Evidence (paste output)**:
```bash
# Test run output:
$ uv run pytest -q tests/test_example_module.py::test_initial_wiring
[[PH:OUTPUT]]
# Symbol/precondition check output:
[[PH:PRECONDITION_OUTPUT]]
```

### Task 1.2 — Baseline capture

TASK_1_2_PATHS=(
  "tests/test_baseline.py"
)

**Status**: 📋 PLANNED

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
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated
**Evidence (paste output)**:
```bash
# Test run output:
$ uv run pytest -q tests/test_baseline.py::test_baseline
[[PH:OUTPUT]]
# Symbol/precondition check output:
[[PH:PRECONDITION_OUTPUT]]
```

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | [[PH:DATE_YYYY_MM_DD]] |
| Repo | example_repo |
| Branch | main |
| Commit | [[PH:GIT_COMMIT]] |
| Runner | uv [[PH:UV_VERSION]] |
| Runtime | Python [[PH:PYTHON_VERSION]] |

**Evidence**:
```bash
$ git rev-parse --abbrev-ref HEAD
[[PH:OUTPUT]]
```

**Baseline tests**:
```bash
$ uv sync
[[PH:OUTPUT]]
$ uv run pytest -q
[[PH:OUTPUT]]
[[PH:OUTPUT]]
```

## Global Clean Table Scan
```bash
$ ! rg 'TODO|FIXME|XXX' src/
# Import hygiene (runner=uv)
$ if rg 'from \.\.' src/; then exit 1; fi
$ if rg 'import \*' src/; then exit 1; fi
# Output placeholder for scan
[[PH:PASTE_CLEAN_TABLE_OUTPUT]]
```

## STOP — Phase Gate
- [ ] All Phase N tasks ✅ COMPLETE
- [ ] Phase N tests pass
- [ ] Global Clean Table scan passes (output pasted above)
- [ ] `.phase-N.complete.json` exists
- [ ] Drift ledger current

## Drift Ledger (append-only)
| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
|      |        |       |          |            |          |

## Phase Unlock Artifact
```bash
$ cat > .phase-1.complete.json << EOF
{
  "phase": 1,
  "completed_at": "[[PH:TS_UTC]]",
  "commit": "[[PH:GIT_COMMIT]]"
}
EOF
$ if rg '\[\[PH:' .phase-1.complete.json; then exit 1; fi
```

## Prose Coverage Mapping
| Prose requirement | Source (file/section) | Implemented by Task(s) |
|-------------------|-----------------------|------------------------|
| Initial wiring | SPEC §0 | 1.1 |
| Baseline capture | SPEC §0 | 1.2 |
