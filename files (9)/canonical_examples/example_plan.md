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
| Prose requirement | Source (file/section) | Implemented by task(s) |
|-------------------|-----------------------|------------------------|
| [[PH:REQ_LABEL]] | [[PH:REQ_SRC]] | [[PH:TASK_IDS]] |
