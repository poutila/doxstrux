---
ai_task_list:
  schema_version: "1.6"
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
| Prose requirement | Source (file/section) | Implemented by task(s) |
|-------------------|-----------------------|------------------------|
| Example requirement | example_spec.md#1 | 1.1 |
