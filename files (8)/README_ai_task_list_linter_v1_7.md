# AI Task List Linter v1.7

Deterministic linter for AI Task Lists (Spec v1.5).

## What's New in v1.7

**All governance rules are now baked in:**

| Governance Document | Enforcement | Status |
|---------------------|-------------|--------|
| TDD_GOVERNANCE | R-ATL-040 (TDD steps), R-ATL-041 (STOP) | ✅ BAKED IN |
| CLEAN_TABLE_PRINCIPLE | R-ATL-042 (checklist), R-ATL-060/061 | ✅ BAKED IN |
| IMPORTS_GOVERNANCE | R-ATL-063 (linter-enforced for Python) | ✅ BAKED IN |
| UV_AS_PACKAGE_MANAGER | R-ATL-071, R-ATL-072, R-ATL-075 | ✅ BAKED IN |
| NO_WEAK_TESTS | R-ATL-041 (4 checklist items) | ✅ BAKED IN |
| RG_AS_SEARCH_TOOL | R-ATL-001, R-ATL-D2, R-ATL-D4 | ✅ BAKED IN |

## Key Changes

**R-ATL-042: Clean Table checklist enforcement**

The linter enforces all 5 Clean Table checklist items in STOP blocks:

```markdown
**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)
```

**R-ATL-063: Import hygiene enforcement (Python projects)**

When `runner: "uv"` and `mode: instantiated`, the Global Clean Table Scan MUST include:

```bash
$ rg 'from \.\.' src/ && exit 1 || true    # No multi-dot relative imports
$ rg 'import \*' src/ && exit 1 || true    # No wildcard imports
```

This is **linter-enforced** for Python projects. Non-Python runners (npm, cargo, go) are exempt.

**Non-negotiable Invariant #7**

Template now includes:
> 7. **Import hygiene** — Absolute imports preferred; no multi-dot relative (`from ..`); no wildcards (`import *`).

## Run

```bash
# Standard lint
uv run python ai_task_list_linter_v1_7.py PROJECT_TASKS.md

# With captured evidence header enforcement (opt-in)
uv run python ai_task_list_linter_v1_7.py --require-captured-evidence PROJECT_TASKS.md
```

Exit codes: 0 = pass, 1 = lint violations, 2 = usage/internal error

## Required YAML Front Matter

```yaml
ai_task_list:
  schema_version: "1.5"    # Must be exactly "1.5"
  mode: "instantiated"     # or "template"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"        # Required
```

## STOP Block Requirements

Every non-Phase-0 task STOP block must have:

1. **No Weak Tests checklist** (4 items) — R-ATL-041
2. **Clean Table checklist** (5 items) — R-ATL-042
3. **Evidence with both labels** — R-ATL-023

## Global Clean Table Scan (Python/uv)

For Python projects (`runner: "uv"`), the Global Clean Table Scan MUST include:

```bash
$ rg 'from \.\.' src/ && exit 1 || true    # R-ATL-063
$ rg 'import \*' src/ && exit 1 || true    # R-ATL-063
```

## Test Results

```
✅ Template v5 passes
✅ Valid v1.5 document with import hygiene passes
✅ Missing Clean Table checklist → FAILS (R-ATL-042)
✅ Missing import hygiene (runner=uv) → FAILS (R-ATL-063)
✅ npm runner without import hygiene → PASSES (exempt)
✅ Schema version 1.4 → REJECTED (requires 1.5)
```

## Migration from v1.6

1. Update `schema_version` to `"1.5"`
2. Add Clean Table checklist to all STOP blocks
3. For Python projects (`runner: "uv"`), add import hygiene patterns to Global Clean Table Scan:
   ```bash
   $ rg 'from \.\.' src/ && exit 1 || true
   $ rg 'import \*' src/ && exit 1 || true
   ```

## Full Rule Set

| Rule | Description |
|------|-------------|
| R-ATL-001 | schema_version == "1.5", search_tool required |
| R-ATL-022 | No placeholders in instantiated mode |
| R-ATL-023 | STOP evidence labels + real output |
| R-ATL-024 | Captured evidence headers (opt-in) |
| R-ATL-040 | TDD steps required |
| R-ATL-041 | No Weak Tests checklist (4 items) |
| R-ATL-042 | Clean Table checklist (5 items) |
| R-ATL-050 | Phase Unlock Artifact cat > pattern |
| R-ATL-063 | **Import hygiene (Python/uv only)** |
| R-ATL-071 | Runner prefix on $ lines |
| R-ATL-072 | UV forbidden patterns |
| R-ATL-075 | $ prefix mandatory |

## Design Philosophy

v1.7 completes the "governance bake-in":

1. **All 6 governance documents** are now reflected in linter/spec/template
2. **Process rules** (checklists) are linter-enforced
3. **Language-specific rules** (import hygiene) are enforced when applicable (runner=uv)
4. **Language-agnostic** for non-Python projects (npm, cargo, go exempt from import hygiene)
