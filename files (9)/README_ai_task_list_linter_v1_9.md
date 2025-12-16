# AI Task List Framework

Deterministic framework for AI task lists (modes: template/plan/instantiated). Versions/schema: see COMMON.md §Version Metadata. <!-- See COMMON.md §Version Metadata -->

## File Index

**Core artifacts:**
- `COMMON.md` — Shared framework definitions (versions, modes, SSOT hierarchy)
- `AI_TASK_LIST_SPEC_v1.md` — Specification (rules, headings, governance)
- `AI_TASK_LIST_TEMPLATE_v6.md` — Template v6 for new task lists
- `ai_task_list_linter_v1_9.py` — Stdlib linter implementing the spec

**Guides:**
- `MANUAL.md` — Framework manual (workflows, checklists, prose conversion)
- `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md` — Runtime prompt for prose → task list

**Workspace:**
- `work_folder/` — Generated task lists
- `canonical_examples/` — Lint-clean examples (template/plan/instantiated)
- `canonical_examples/negatives/` — Expected-fail fixtures for regression
- `task_list_archive/` — Planning/support docs kept for reference

## Run

```bash
# Standard lint
uv run python ai_task_list_linter_v1_9.py PROJECT_TASKS.md

# With captured evidence header enforcement
uv run python ai_task_list_linter_v1_9.py --require-captured-evidence PROJECT_TASKS.md

# Recommended for CI (instantiated lists)
uv run python ai_task_list_linter_v1_9.py --require-captured-evidence PROJECT_TASKS.md
```

Exit codes: 0 = pass, 1 = lint violations, 2 = usage/internal error

## Required YAML Front Matter

```yaml
ai_task_list:
  schema_version: "<see COMMON.md §Version Metadata>"    # Do not hard-code; use the value from COMMON.md
  mode: "plan"             # or "template" / "instantiated"
  runner: "uv"
  runner_prefix: "uv run"  # REQUIRED; used for runner enforcement
  search_tool: "rg"        # REQUIRED; rg vs grep enforcement
```

## Test Results

```
✅ Template v6 passes (template mode)
✅ Plan example passes
✅ Instantiated example passes (--require-captured-evidence)
✅ Comment compliance REJECTED (import hygiene patterns in comments)
✅ Comment compliance REJECTED (Phase Unlock scan in comments)
✅ schema_version enforcement: must match COMMON.md tuple; mismatches fail
✅ Spec search_tool consistency (MUST include, not MAY)
```

## Mode Usage

See COMMON.md §Mode Definitions for mode semantics. See MANUAL.md for workflows, checklists, and common mistakes.

## Limitations

The linter enforces structure and presence of output but cannot cryptographically prove provenance. See MANUAL.md §10 for details. Recommended: make `--require-captured-evidence` mandatory in CI for instantiated lists.
