# AI Task List Linter v1.2 (minimal update)

This is the v1 linter plus two additional deterministic checks:

## D2 — Preconditions symbol check enforcement
For **non-Phase-0 tasks**:
- Template mode: Preconditions fenced code block must include `[[PH:SYMBOL_CHECK_COMMAND]]`
- Instantiated mode: Preconditions fenced code block must include a `rg` or `grep` command

## D3 — Drift Ledger Evidence witness format
In **instantiated mode**, any non-empty Drift Ledger row must include a `path:line` witness in the Evidence cell
(e.g., `src/module.py:123` or `docs/README.md:45`). Fully empty rows are allowed.

## Run

    uv run python ai_task_list_linter_v1_2.py PROJECT_TASKS.md

JSON:

    uv run python ai_task_list_linter_v1_2.py --json PROJECT_TASKS.md
