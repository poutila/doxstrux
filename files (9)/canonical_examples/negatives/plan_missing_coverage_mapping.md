---
ai_task_list:
  schema_version: "1.6"
  mode: "plan"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# Plan Negative Fixture — Missing Prose Coverage Mapping (R-ATL-PROSE)

Task ID N.M → TASK_N_M_PATHS

## Non-negotiable Invariants
## Placeholder Protocol
## Source of Truth Hierarchy
## Phase 0 — Baseline Reality
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
```

## Global Clean Table Scan
```bash
$ ! rg 'TODO|FIXME|XXX' src/
$ if rg 'from \.\.' src/; then exit 1; fi
$ if rg 'import \*' src/; then exit 1; fi
[[PH:OUTPUT]]
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
$ rg '\[\[PH:' .phase-1.complete.json
```

## Phase 1 — Demo

### Task 1.1 — Demo
TASK_1_1_PATHS=(
  "src/demo.py"
)
**Status**: 📋 PLANNED

#### Preconditions
```bash
$ rg demo_symbol src/
```

### TDD Step 1 — Write test (RED)
```bash
$ uv run pytest -k demo_test_should_fail
[[PH:OUTPUT]]
```

### TDD Step 2 — Implement (minimal)
```bash
$ uv run pytest -k demo_test_should_fail
[[PH:OUTPUT]]
```

### TDD Step 3 — Verify (GREEN)
```bash
$ uv run pytest -k demo_test_should_fail
[[PH:OUTPUT]]
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
- [ ] Clean Table verified
- [ ] STOP evidence pasted above

### STOP — Evidence
```bash
# Test run output:
# cmd: uv run pytest -k demo_test_should_fail
[[PH:OUTPUT]]

# Symbol/precondition check output:
# cmd: uv run ruff check src/demo.py
[[PH:OUTPUT]]
```
