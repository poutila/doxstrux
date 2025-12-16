<!--
  CANONICAL EXAMPLE: Template Mode

  This is a MINIMAL lint-passing example for template mode.
  Not the full AI_TASK_LIST_TEMPLATE_v6.md - see that for the complete template.

  Purpose: Regression test for linter - this file MUST pass lint.
  Run: uv run python tools/ai_task_list_linter_v1_9.py canonical_examples/example_template.md
-->
---
ai_task_list:
  schema_version: "1.7"
  mode: "template"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# Example Template Task List (Mode: template)

Task ID N.M → TASK_N_M_PATHS

## Non-negotiable Invariants

## Placeholder Protocol

## Source of Truth Hierarchy

## Phase 0 — Baseline Reality

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | [[PH:DATE_YYYY_MM_DD]] |
| Repo | [[PH:REPO_NAME]] |
| Branch | [[PH:GIT_BRANCH]] |
| Commit | [[PH:GIT_COMMIT]] |
| Runner | [[PH:RUNNER_NAME_VERSION]] |
| Runtime | [[PH:RUNTIME_VERSION]] |

**Evidence**:
```bash
$ [[PH:BASELINE_COMMAND]]
[[PH:OUTPUT]]
```

**Baseline tests**:
```bash
$ [[PH:BASELINE_TEST_COMMAND]]
[[PH:OUTPUT]]
```

## Global Clean Table Scan
```bash
$ [[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]
[[PH:PASTE_CLEAN_TABLE_OUTPUT]]
```

## Drift Ledger (append-only)
| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
|      |        |       |          |            |          |

## Phase Unlock Artifact
```bash
# Phase unlock placeholder (template)
# cat > .phase-N.complete.json << EOF
# {
#   "phase": N,
#   "completed_at": "[[PH:TS_UTC]]",
#   "commit": "[[PH:GIT_COMMIT]]"
# }
# EOF
```

## STOP — Phase Gate
- [ ] `.phase-N.complete.json` exists
- [ ] Global Clean Table scan passes (output pasted above)
- [ ] Phase N tests pass
- [ ] Drift ledger current

## STOP — Phase Gate
- [ ] All Phase N tasks ✅ COMPLETE
- [ ] Phase N tests pass
- [ ] Global Clean Table scan passes (output pasted above)
- [ ] `.phase-N.complete.json` exists
- [ ] Drift ledger current
