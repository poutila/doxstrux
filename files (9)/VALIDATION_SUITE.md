# Validation Suite — Plan Mode Rollout (Spec v1.7 / Linter v1.9)

## Tests to Run

### 1) Template scaffold
- Input: `AI_TASK_LIST_TEMPLATE_v6.md` (template mode)
- Command: `uv run python ai_task_list_linter_v1_8.py AI_TASK_LIST_TEMPLATE_v6.md`
- Expected: exit 0 (structure/placeholders allowed)

### 2) Plan artifact
- Input: `canonical_examples/example_plan.md` (plan mode)
- Command: `uv run python ai_task_list_linter_v1_8.py canonical_examples/example_plan.md`
- Expected: exit 0 (real commands, evidence placeholders)

### 3) Instantiated sample
- Input: `canonical_examples/example_instantiated.md` (instantiated mode)
- Command: `uv run python ai_task_list_linter_v1_8.py --require-captured-evidence canonical_examples/example_instantiated.md`
- Expected: exit 0 (no placeholders; real evidence; captured headers present)

### 4) Negative cases
- Plan with command placeholders:
  - Mutate a plan file to include `[[PH:SYMBOL_CHECK_COMMAND]]` in Preconditions.
  - Expected: exit 1, R-ATL-D2 (plan forbids command placeholders).
- Template with bad gates:
  - Insert `rg ... && exit 1 || echo` into Global Clean Table.
  - Expected: exit 1 (missing placeholder / pattern per template rules).
- Coverage mapping missing (plan):
  - Remove `## Prose Coverage Mapping` from a plan file.
  - Expected: exit 1, R-ATL-PROSE.

### 5) Doc-sync spot check
- Ensure mode references are consistent:
  - Files: spec, template, orchestrator, manuals, README, DESCRIPTION, INDEX, MIGRATION_GUIDE.
  - Quick grep: `rg "mode: \\\"plan\\\"|mode: \\\"template\\\"|mode: \\\"instantiated\\\"" (specify files as needed)`

## Test Results (as of this run)
- AI_TASK_LIST_TEMPLATE_v6.md: pass (exit 0)
- canonical_examples/example_plan.md: pass (exit 0)
- canonical_examples/example_instantiated.md: pass (exit 0) with `--require-captured-evidence`

## Performance/Regression Checks
- Target: <10% overhead vs prior run (manual observation).
- Backward-compat: run linter on a known v1.5/v1.6 task list; expected behavior: errors for schema/spec mismatch.

## Release Artifacts
- CHANGELOG: add entry for spec v1.7/linter v1.9 (plan mode, baseline/Phase Gate enforcement, coverage check).
- Migration: ensure `MIGRATION_GUIDE.md` is up to date and linked from README.
