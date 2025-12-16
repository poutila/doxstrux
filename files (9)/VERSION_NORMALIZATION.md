# VERSION_NORMALIZATION.md — Plan to Normalize Version Metadata

Goal: One consistent version story across all framework artifacts.
Target SSOT:
- Spec: v1.9
- schema_version: "1.7"
- Linter: ai_task_list_linter_v1_9.py (LINTER_VERSION = 1.9.0)
- Template: v6.0
- Modes: template / plan / instantiated

## Scope (what to fix)
- AI_TASK_LIST_SPEC_v1.md: header/banner, rule IDs (use R-ATL-NEW-01/02/03), placeholders spelled out (no `...`).
- COMMON.md: Version metadata, mode definitions, runner/import/evidence rules.
- Linter: ai_task_list_linter_v1_9.py banner text; ensure version string matches LINTER_VERSION; rule IDs consistent with spec.
- README_ai_task_list_linter_v1_9.md: Header/body to Spec v1.9, schema 1.7, linter v1_9.
- Manuals: USER_MANUAL.md, AI_ASSISTANT USER_MANUAL.md, PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md — version/mode/schema references.
- Template: AI_TASK_LIST_TEMPLATE_v6.md — note Spec v1.9/schema 1.7, three-mode context.
- Validation suite: VALIDATION_SUITE.md — refer to Spec/Linter v1.9.
- Index: INDEX.md — Spec/Linter/README paths and versions.
- CHANGELOG: ensure v1.9 entry matches above.
- Optional: Archived docs (task_list_archive, etc.) — mark as legacy or leave untouched; do not confuse SSOT.

## Search/replace commands (read-only, to locate)
- Find stale version strings:
  - `rg 'schema_version: \"1\\.6\"' files\\ \\(9\\)`
  - `rg 'Spec v1\\.7' files\\ \\(9\\)`
  - `rg 'ai_task_list_linter_v1_8' files\\ \\(9\\)`
  - `rg 'README_ai_task_list_linter_v1_8' files\\ \\(9\\)`
- Check mode mentions:
  - `rg 'mode: \"template\"|mode: \"plan\"|mode: \"instantiated\"' files\\ \\(9\\)`
- Check linter banner/version:
  - `rg 'LINTER_VERSION|Spec v1\\.9|schema_version 1\\.7' files\\ \\(9\\)/ai_task_list_linter_v1_9.py`

## Edits to perform (content-level)
1) Spec:
   - Header: Spec v1.9; schema_version "1.7".
   - Rule IDs: use R-ATL-NEW-01/02/03 (no PROSE/031 drift).
   - Remove non-pattern ellipses.
2) COMMON:
   - Version block: Spec v1.9, schema 1.7, linter v1_9, template v6.0.
   - Mode table: template/plan/instantiated, placeholders spelled out.
3) Linter:
   - Banner text: Spec v1.9; schema_version 1.7; three modes.
   - LINTER_VERSION = 1.9.0; ensure docstring reflects it.
4) README_ai_task_list_linter_v1_9.md:
   - Header/body: Spec v1.9; schema 1.7; linter v1_9; three modes.
5) Manuals (USER_MANUAL.md, AI_ASSISTANT USER_MANUAL.md, PROMPT_ORCHESTRATOR):
   - Version references → Spec v1.9/schema 1.7; linter v1_9.
6) Template:
   - Note Spec v1.9/schema 1.7; $-prefixed commands; three-mode context.
7) VALIDATION_SUITE.md:
   - Header/commands refer to v1.9.
8) INDEX.md:
   - Spec v1.9/schema 1.7; linter README v1_9; linter file v1_9.
9) CHANGELOG:
   - Ensure v1.9 entry matches the above.

## Definition of Done
- `rg 'schema_version: \"1\\.6\"|Spec v1\\.7|ai_task_list_linter_v1_8|README_ai_task_list_linter_v1_8' files\\ \\(9\\)` returns nothing.
- All targeted files explicitly state Spec v1.9, schema_version "1.7", linter v1_9.
- Linter banner matches LINTER_VERSION; rule IDs in spec and linter align (NEW-01/02/03).
- Validation suite headers/commands refer to v1.9.
- No non-pattern `...` truncations remain in SSOT docs (spec/COMMON/manuals/template).
