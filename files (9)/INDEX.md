# AI Task List Framework — File Index

Core artifacts:
- `COMMON.md` — Shared framework definitions (versions, modes, SSOT, runner/import/gate/placeholder/evidence rules).
- `AI_TASK_LIST_SPEC_v1.md` — Specification for AI task lists (rules, headings, governance; template/plan/instantiated; see COMMON.md §Version Metadata for versions/schema). <!-- See COMMON.md §Version Metadata -->
- `AI_TASK_LIST_TEMPLATE_v6.md` — Template v6 for new task lists.
- `ai_task_list_linter_v1_9.py` — Stdlib linter implementing the spec (three modes; `--require-captured-evidence` support). See COMMON.md §Version Metadata for versions/schema.
- `README_ai_task_list_linter_v1_9.md` — Linter release notes and usage.

Guides and manuals:
- `USER_MANUAL.md` — Framework user manual (spec/template/linter usage, workflows, checklists).
- `AI_ASSISTANT USER_MANUAL.md` — AI-oriented manual for converting prose to task lists (template vs instantiated, gates, coverage).
- `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md` — Runtime prompt for prose → AI task list generation (plan-mode output).
- `INDEX.md` — This file (index of framework artifacts).

Workspace:
- `work_folder/` — Place to store generated task lists (e.g., `<label>_TASKS_template.md`); contains `.gitkeep` (tracked).
- `canonical_examples/` — Lint-clean examples for template/plan/instantiated.
- `canonical_examples/negatives/` — Expected-fail fixtures for regression (coverage missing, plan placeholder, template Clean Table placeholder).
- `task_list_archive/` — Planning/support docs kept for reference (IMPLEMENTING_COMMON.md, COMMON_MD_QUICK_GUIDE.md, FIXES_STATUS.md, MIGRATION_GUIDE.md).
