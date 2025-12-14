# AI Task List Linter v1

## Run

Human-readable diagnostics:

    uv run python ai_task_list_linter_v1.py PROJECT_TASKS.md

JSON report:

    uv run python ai_task_list_linter_v1.py --json PROJECT_TASKS.md

Exit codes:
- 0 = pass
- 1 = lint violations
- 2 = usage/internal error

## What it enforces (high level)

- YAML front matter: ai_task_list.schema_version/mode/runner/runner_prefix
- Required headings
- Placeholder rules:
  - template mode: placeholders allowed
  - instantiated mode: placeholders forbidden (including paste slots)
- Phase/Task structure and uniqueness
- Per-task canonical TASK_N_M_PATHS array + required TDD/STOP headings
- No Weak Tests prompts
- Drift Ledger table columns
- Global Clean Table Scan hooks
- Runner checks (and UV-specific forbiddens)

This is intentionally syntax-first and deterministic.
