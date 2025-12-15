# Validation Suite — Plan Mode Rollout (Spec v1.9 / Linter v1.9)

## Tests to Run

### 1) Template scaffold
- Input: `AI_TASK_LIST_TEMPLATE_v6.md` (template mode)
- Command: `uv run python ai_task_list_linter_v1_9.py AI_TASK_LIST_TEMPLATE_v6.md`
- Expected: exit 0 (structure/placeholders allowed)

### 2) Plan artifact
- Input: `canonical_examples/example_plan.md` (plan mode)
- Command: `uv run python ai_task_list_linter_v1_9.py canonical_examples/example_plan.md`
- Expected: exit 0 (real commands, evidence placeholders)

### 3) Instantiated sample
- Input: `canonical_examples/example_instantiated.md` (instantiated mode)
- Command: `uv run python ai_task_list_linter_v1_9.py --require-captured-evidence canonical_examples/example_instantiated.md`
- Expected: exit 0 (no placeholders; real evidence; captured headers present)

### 4) Negative cases (persistent fixtures)
- Plan with command placeholder: `canonical_examples/negatives/plan_preconditions_placeholder.md`
  - Expected: exit 1, R-ATL-D2 (plan forbids `[[PH:SYMBOL_CHECK_COMMAND]]`; requires real rg).
- Plan missing coverage mapping: `canonical_examples/negatives/plan_missing_coverage_mapping.md`
  - Expected: exit 1, R-ATL-PROSE (coverage section missing).
- Template missing Clean Table placeholder: `canonical_examples/negatives/template_missing_clean_table_placeholder.md`
  - Expected: exit 1, R-ATL-060 (placeholder absent in template mode).

### 5) Doc-sync spot check
- Ensure mode references are consistent:
  - Files: spec, template, orchestrator, manuals, README, DESCRIPTION, INDEX, MIGRATION_GUIDE.
  - Quick grep: `rg "mode: \\\"plan\\\"|mode: \\\"template\\\"|mode: \\\"instantiated\\\"" (specify files as needed)`

## Test Results (as of this run)
- AI_TASK_LIST_TEMPLATE_v6.md: pass (exit 0)
- canonical_examples/example_plan.md: pass (exit 0)
- canonical_examples/example_instantiated.md: pass (exit 0) with `--require-captured-evidence`
- Negative: Plan missing Prose Coverage Mapping (`canonical_examples/negatives/plan_missing_coverage_mapping.md`) → exit 1 (R-ATL-PROSE).
- Negative: Template with missing Clean Table placeholder (`canonical_examples/negatives/template_missing_clean_table_placeholder.md`) → exit 1 (R-ATL-060).
- Negative: Plan with Preconditions placeholder (`canonical_examples/negatives/plan_preconditions_placeholder.md`) → exit 1 (R-ATL-D2) with no crash.

## Performance/Regression Checks
- Target: <10% overhead vs prior run (manual observation).
- Backward-compat: run linter on a known v1.5/v1.6 task list; expected behavior: errors for schema/spec mismatch.

## Release Artifacts
- CHANGELOG: add entry for spec v1.7/linter v1.9 (plan mode, baseline/Phase Gate enforcement, coverage check).
- Migration: ensure `MIGRATION_GUIDE.md` is up to date and linked from README.
