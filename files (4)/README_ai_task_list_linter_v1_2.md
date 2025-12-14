# AI Task List Linter v1.2

## Run

```bash
uv run python ai_task_list_linter_v1_2.py PROJECT_TASKS.md
```

JSON output:

```bash
uv run python ai_task_list_linter_v1_2.py --json PROJECT_TASKS.md
```

Exit codes:
- 0 = pass
- 1 = lint violations
- 2 = usage/internal error

## What's New in v1.2

### D2 — Preconditions symbol-check enforcement

For **non-Phase-0 tasks**:
- **Template mode**: Preconditions fenced code block must include `[[PH:SYMBOL_CHECK_COMMAND]]`
- **Instantiated mode**: Preconditions fenced code block must include a `rg` command (or `grep` if search_tool != "rg")

### D3 — Drift Ledger Evidence witness format

In **instantiated mode**, any non-empty Drift Ledger row must include a `path:line` witness in the Evidence cell (e.g., `src/module.py:123`). Fully empty rows are allowed.

### D4 — search_tool enforcement (ripgrep preferred)

When `search_tool: rg` is set in YAML front matter:
- All text searches must use `rg` (ripgrep)
- `grep` is forbidden in code blocks
- D2 Preconditions must use `rg`

### Additional Fixes

- **Phase 0 exemption**: Bootstrap tasks (Phase 0) are exempt from TDD/STOP requirements
- **YAML comments**: Inline comments now stripped correctly (e.g., `mode: "template"  # comment`)
- **Required headings**: Now includes `## Phase Unlock Artifact` (9 total)

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
| R-ATL-030 | Phase 0 required |
| R-ATL-031 | Task ID uniqueness |
| R-ATL-032 | Canonical `TASK_N_M_PATHS` array |
| R-ATL-040 | TDD headings (Phase 1+ only) |
| R-ATL-041 | STOP block + No Weak Tests (Phase 1+ only) |
| R-ATL-060 | Global Clean Table Scan hooks |
| R-ATL-061 | Global scan evidence in instantiated mode |
| R-ATL-071 | Runner prefix consistency |
| R-ATL-072 | UV-specific enforcement |
| R-ATL-080 | Drift Ledger table columns |
| R-ATL-D2 | Preconditions symbol-check command |
| R-ATL-D3 | Drift Ledger Evidence witness format |
| R-ATL-D4 | search_tool=rg forbids grep |

## Design Notes

- **stdlib only** — no external dependencies
- **deterministic** — no network, no repo mutation
- **Phase 0 exempt** — bootstrap tasks don't require TDD/STOP blocks
- **Comment-aware** — D2 skips bash comment lines when checking for rg/grep
- **ripgrep preferred** — set `search_tool: rg` to enforce rg-only searches

## Example Output

Human-readable:
```
PROJECT_TASKS.md:42:R-ATL-D2:Task 1.1 Preconditions must include rg command (search_tool=rg).
PROJECT_TASKS.md:56:R-ATL-D4:grep is forbidden when search_tool=rg. Use ripgrep (rg) instead.
```

JSON:
```json
{
  "passed": false,
  "error_count": 2,
  "errors": [
    {"line": 42, "rule_id": "R-ATL-D2", "message": "..."},
    {"line": 56, "rule_id": "R-ATL-D4", "message": "..."}
  ],
  "mode": "instantiated",
  "runner": "uv",
  "search_tool": "rg",
  "schema_version": "1.0"
}
```
