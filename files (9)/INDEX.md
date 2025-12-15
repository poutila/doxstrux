# AI Task List Framework — File Index

Core artifacts:
- `AI_TASK_LIST_SPEC_v1.md` — Specification v1.7 for AI task lists (rules, headings, governance; adds plan mode; schema_version stays 1.6). <!-- See COMMON.md §Version Metadata -->
- `AI_TASK_LIST_TEMPLATE_v6.md` — Template v6 for new task lists.
- `ai_task_list_linter_v1_8.py` — Stdlib linter implementing Spec v1.7 (code filename unchanged; `--require-captured-evidence` support).
- `README_ai_task_list_linter_v1_8.md` — Linter release notes and usage.

Guides and manuals:
- `USER_MANUAL.md` — Framework user manual (spec/template/linter usage, workflows, checklists).
- `AI_ASSISTANT USER_MANUAL.md` — AI-oriented manual for converting prose to task lists (template vs instantiated, gates, coverage).
- `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md` — Runtime prompt for prose → AI task list generation (plan-mode output).
- `DESCRIPTION.md` — Overview of the framework purpose and goals.
- `INDEX.md` — This file (index of framework artifacts).

Workspace:
- `work_folder/` — Place to store generated task lists (e.g., `<label>_TASKS_v1_template.md`); contains `.gitkeep` (tracked).
- `canonical_examples/` — Lint-clean examples for template/plan/instantiated.
- `canonical_examples/negatives/` — Expected-fail fixtures for regression (coverage missing, plan placeholder, template Clean Table placeholder).
