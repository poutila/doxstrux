# Migration Guide — v1.7/v1.9 (plan mode rollout)

## Scope
- Spec v1.7 (schema_version stays "1.6", plan mode added)
- Linter v1.9 (code filename unchanged)
- Template/Orchestrator/Manuals updated to three-mode lifecycle

## Decision Tree (which mode?)
- `template`: generic scaffold with command/evidence placeholders; reusable across projects.
- `plan`: project-specific planning; commands real; evidence/output placeholders allowed.
- `instantiated`: execution/evidence; no placeholders.

## How to migrate existing task lists
1) Identify files with real commands but `mode: "template"`:
   ```bash
   rg 'mode:\\s*\"template\"' --files-with-matches | xargs rg '^\\$' -l
   ```
2) For project-specific lists with real commands:
   - Change `mode: "template"` → `mode: "plan"`.
   - Keep real commands; keep evidence placeholders.
   - Add Prose Coverage Mapping if missing (recommended; now linted as error when missing/malformed).
3) For generic scaffolds:
   - Keep `mode: "template"`.
   - Ensure command placeholders (`[[PH:SYMBOL_CHECK_COMMAND]]`, `[[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]`) remain.
4) For executed lists:
   - Keep/flip to `mode: "instantiated"` only with real evidence and no placeholders.

## Deprecation timeline (recommended)
- v1.6.1: add plan mode; template relaxed (warnings if applicable).
- v1.7.0: enforce strict template (fail on concrete commands); plan mode required for real-command plans.
- Grace period: ~8 weeks between warn → fail.

## Validation checklist (post-migration)
- Lint template: `uv run python ai_task_list_linter_v1_8.py canonical_examples/example_template.md`
- Lint plan: `uv run python ai_task_list_linter_v1_8.py canonical_examples/example_plan.md`
- Lint instantiated: `uv run python ai_task_list_linter_v1_8.py --require-captured-evidence canonical_examples/example_instantiated.md`
- Run on your migrated file: `uv run python ai_task_list_linter_v1_8.py <your_file.md>`

## Notes
- Prose Coverage Mapping: missing/empty is an error in plan/instantiated; malformed/invalid anchors also error.
- Gates: linter enforces presence; shell exit semantics are process-level (CI/authoring).
- Examples: see `canonical_examples/` for lint-clean reference files.
