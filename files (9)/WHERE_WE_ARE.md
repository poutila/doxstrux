# WHERE_WE_ARE.md

> **Date**: 2025-12-17
> **Purpose**: Track current status of AI Task List Framework end-to-end testing

---

## Overview

This directory contains the AI Task List Framework specifications and templates being validated with SPEKSI-generated linters.

---

## Pipeline Test Status

| Stage | Tool | Status | Errors |
|-------|------|--------|--------|
| Input Validation | `prose_input_linter.py` | PASS | 0 |
| Conversion | AI (manual) | PASS | - |
| Output Validation | `ai_task_list_linter.py` | BLOCKED | 30 (22 false positive) |

---

## Test Artifacts

| File | Role | Status |
|------|------|--------|
| `PYDANTIC_SCHEMA.md` | Input (prose format) | Fixed, passes linter |
| `PYDANTIC_SCHEMA_TASKS.md` | Output (task list format) | Created, blocked by BUG-006 |
| `PYDANTIC_SCHEMA_known_bad_v2.txt` | Baseline (96 errors) | Reference |
| `PYDANTIC_SCHEMA_fixed_v2.txt` | Fixed baseline (0 errors) | Reference |

---

## Bug Discovery Progress

Testing revealed 6 bugs in SPEKSI core, 5 fixed:

| Bug | Status | Description |
|-----|--------|-------------|
| BUG-001 | FIXED | YAML enum field validation scanned entire document |
| BUG-002 | FIXED | Prefix check used literal rule text instead of backtick content |
| BUG-003 | FIXED | Block existence check created double colon pattern |
| BUG-004 | FIXED | Decision table check triggered on non-decision tables |
| BUG-005 | FIXED | Heading pattern validation matched every line (678 errors) |
| BUG-006 | **OPEN** | Heading pattern checks all `##` headings, not just `## Phase` |

### Error Reduction Timeline

```
Initial:     496 errors (before BUG-001/002/003 fixes)
After fixes:  96 errors (BUG-001/002/003 fixed)
Input fixed:   0 errors (document corrected)
Output run:  678 errors (BUG-005 present)
BUG-005 fix:  34 errors (scoping to heading level)
BUG-006 fix:  30 errors (partial - prefix filtering incomplete)
Expected:    ~8 errors (after BUG-006 fully resolved)
```

---

## Current Blockers

### BUG-006: Heading Prefix Filtering

**Problem**: After BUG-005 fix, R-ATL-030 correctly checks only `##` headings, but it checks ALL `##` headings against the `## Phase N — Title` pattern.

**False Positives** (22 errors):
- `## Non-negotiable Invariants` - NOT a Phase heading
- `## Baseline Snapshot` - NOT a Phase heading
- `## STOP — Phase 1 Gate` - NOT a Phase heading (STOP prefix)
- `## Drift Ledger` - NOT a Phase heading
- `## Global Clean Table Scan` - NOT a Phase heading
- `## Phase Unlock Artifact` - Missing number in pattern
- 16x `### TDD Step` / `### STOP` - NOT Task headings

**Solution**: Extend `HeadingLinesScope` to filter by prefix:
```python
HeadingLinesScope(level=2, prefix="Phase")  # Only "## Phase ..." headings
HeadingLinesScope(level=3, prefix="Task")   # Only "### Task ..." headings
```

---

## Legitimate Remaining Errors (After BUG-006 Fix)

Expected ~8 errors that need document fixes:

| Rule | Count | Issue |
|------|-------|-------|
| R-ATL-020 | 2 | Table column structure |
| R-ATL-080 | 2 | Drift Ledger column requirements |
| R-ATL-075 | 1 | Document start format |
| R-ATL-011/063/072 | 3 | Missing content sections |

---

## Next Steps

1. **Fix BUG-006**: Add prefix parameter to `HeadingLinesScope`
2. **Re-run output linter**: Verify error count drops to ~8
3. **Fix document errors**: Correct the ~8 legitimate issues
4. **Complete E2E test**: Achieve 0 errors on output validation

---

## Files in This Directory

| File | Type | Purpose |
|------|------|---------|
| `GOAL.md` | Spec | Framework goal definition |
| `COMPLETE_VALIDATION.md` | Doc | Pipeline documentation |
| `WHERE_WE_ARE.md` | Doc | This file - current status |
| `PROSE_INPUT_SPEC.md` | Spec | Rules for prose input format |
| `PROSE_INPUT_TEMPLATE.md` | Template | Input template |
| `AI_TASK_LIST_SPEC.md` | Spec | Rules for task list format |
| `AI_TASK_LIST_TEMPLATE.md` | Template | Output template |
| `PYDANTIC_SCHEMA.md` | Test | Test input (passes) |
| `PYDANTIC_SCHEMA_TASKS.md` | Test | Test output (blocked) |
| `PROMPT_*.md` | Prompts | AI prompts for pipeline stages |

---

## SPEKSI Integration

Linters are generated from specs in:
- `/home/lasse/Dropbox/python/omat/SPEKSI/src/speksi/generated/PROSE_INPUT_SPEC/`
- `/home/lasse/Dropbox/python/omat/SPEKSI/src/speksi/generated/AI_TASK_LIST_SPEC/`

Bug tracking: `/home/lasse/Dropbox/python/omat/SPEKSI/BUGS.md`

---

**Last Updated**: 2025-12-17
