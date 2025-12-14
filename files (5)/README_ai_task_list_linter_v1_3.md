# AI Task List Linter v1.3

Deterministic linter for AI Task Lists (Spec v1.1).

## Run

```bash
uv run python ai_task_list_linter_v1_3.py PROJECT_TASKS.md
```

JSON output:

```bash
uv run python ai_task_list_linter_v1_3.py --json PROJECT_TASKS.md
```

Exit codes:
- 0 = pass
- 1 = lint violations
- 2 = usage/internal error

## What's New in v1.3 (Spec v1.1)

### Eliminates "blank evidence" loophole

**R-ATL-023**: Non-empty evidence required in instantiated mode
- Baseline Snapshot: Each `$ command` must have non-empty output
- STOP evidence: Must contain actual test/precondition output
- Global Clean Table: Evidence block must be non-empty

### D4 fix: Code-block-only grep detection

Grep detection now **only** flags `grep` usage inside fenced code blocks.
- ✅ Prose like "we use rg instead of grep" is NOT flagged
- ❌ `grep pattern file` inside code blocks IS flagged

### R-ATL-033: Naming rule enforcement

Document must state the naming convention once:
```
> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS`
```

### R-ATL-071: Strengthened runner enforcement

Runner prefix checked on **all** runner-managed commands in code blocks:
- Commands requiring prefix: `pytest`, `python`, `mypy`, `ruff`, `black`, `isort`
- Exempt commands: `git`, `rg`, `grep`, `cd`, `ls`, `cat`, `echo`, `test`, etc.

## Rules Enforced

| Rule | Description |
|------|-------------|
| R-ATL-001 | YAML front matter with `ai_task_list` block |
| R-ATL-002 | Mode semantics (template vs instantiated) |
| R-ATL-003 | Placeholder syntax `[[PH:NAME]]` |
| R-ATL-010 | Required headings (9 total) |
| R-ATL-020 | Baseline Snapshot table rows |
| R-ATL-021 | Baseline Evidence marker |
| R-ATL-022 | No evidence placeholders in instantiated mode |
| **R-ATL-023** | **Non-empty evidence in instantiated mode (NEW)** |
| R-ATL-030 | Phase 0 required |
| R-ATL-031 | Task ID uniqueness |
| R-ATL-032 | Canonical `TASK_N_M_PATHS` array |
| **R-ATL-033** | **Naming rule stated once (NEW)** |
| R-ATL-040 | TDD headings (Phase 1+ only) |
| R-ATL-041 | STOP block + No Weak Tests (Phase 1+ only) |
| R-ATL-060 | Global Clean Table Scan hooks |
| R-ATL-061 | Global scan evidence in instantiated mode |
| **R-ATL-071** | **Runner prefix on all runner commands (STRENGTHENED)** |
| R-ATL-072 | UV-specific enforcement |
| R-ATL-080 | Drift Ledger table columns |
| R-ATL-D2 | Preconditions symbol-check command |
| R-ATL-D3 | Drift Ledger Evidence witness format |
| **R-ATL-D4** | **search_tool=rg forbids grep in code blocks only (FIXED)** |

## Design Notes

- **stdlib only** — no external dependencies
- **deterministic** — no network, no repo mutation
- **Phase 0 exempt** — bootstrap tasks don't require TDD/STOP blocks
- **Comment-aware** — D2 skips bash comment lines when checking for rg/grep
- **Code-block-aware** — D4 and R-ATL-071 only check inside fenced code blocks

## Test Coverage

```bash
# D4 prose false positive (should PASS)
python ai_task_list_linter_v1_3.py doc_with_grep_in_prose.md  # ✅ PASS

# Empty evidence (should FAIL)
python ai_task_list_linter_v1_3.py doc_with_empty_evidence.md  # ❌ R-ATL-023

# grep in code block (should FAIL when search_tool=rg)
python ai_task_list_linter_v1_3.py doc_with_grep_in_code.md  # ❌ R-ATL-D4

# Missing naming rule (should FAIL)
python ai_task_list_linter_v1_3.py doc_without_naming_rule.md  # ❌ R-ATL-033

# pytest without runner prefix (should FAIL)
python ai_task_list_linter_v1_3.py doc_with_bare_pytest.md  # ❌ R-ATL-071
```

## Example Output

Human-readable:
```
PROJECT_TASKS.md:30:R-ATL-023:Baseline Snapshot evidence: command(s) missing output.
PROJECT_TASKS.md:58:R-ATL-D4:grep is forbidden when search_tool=rg. Use ripgrep (rg) instead.
PROJECT_TASKS.md:9:R-ATL-033:Missing naming rule statement.
```

JSON:
```json
{
  "passed": false,
  "error_count": 3,
  "errors": [
    {"line": 30, "rule_id": "R-ATL-023", "message": "..."},
    {"line": 58, "rule_id": "R-ATL-D4", "message": "..."},
    {"line": 9, "rule_id": "R-ATL-033", "message": "..."}
  ],
  "mode": "instantiated",
  "runner": "uv",
  "search_tool": "rg",
  "schema_version": "1.1"
}
```

## Migration from v1.2

1. Update `schema_version` from `"1.0"` to `"1.1"` in YAML front matter
2. Ensure all evidence blocks have actual content (not just removed placeholders)
3. Add naming rule statement if missing
4. Review all code blocks for bare runner commands (add prefix)
