# VERSION_NORMALIZATION.md — Plan to Normalize Version Metadata

Goal: One consistent version story across all framework artifacts.
SSOT policy: COMMON.md carries the only canonical version tuple; other docs should either reference COMMON.md or stay silent on concrete numbers.
Target tuple in COMMON.md:
- Spec: v1.9
- schema_version: "1.7"
- Linter: ai_task_list_linter_v1_9.py (LINTER_VERSION = 1.9.0)
- Template: v6.0
- Modes: template / plan / instantiated

## Scope (what to fix)
- AI_TASK_LIST_SPEC_v1.md: header/banner, rule IDs (use R-ATL-NEW-01/02/03), placeholders spelled out (no `...` in normative text).
- COMMON.md: Version metadata (the SSOT tuple), mode definitions, runner/import/evidence rules.
- Linter: ai_task_list_linter_v1_9.py banner text; ensure version string matches LINTER_VERSION; rule IDs consistent with spec.
- README_ai_task_list_linter_v1_9.md: Header/body to Spec v1.9, schema 1.7, linter v1_9.
- Manuals: USER_MANUAL.md, AI_ASSISTANT USER_MANUAL.md, PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md — version/mode/schema references.
- Template: AI_TASK_LIST_TEMPLATE_v6.md — note Spec v1.9/schema 1.7, three-mode context.
- Validation suite: VALIDATION_SUITE.md — refer to Spec/Linter v1.9.
- Index: INDEX.md — Spec/Linter/README paths and versions.
- CHANGELOG: ensure v1.9 entry matches above.
- Optional: Archived docs (task_list_archive, etc.) — mark as legacy or leave untouched; do not confuse SSOT.

## Search/replace commands (read-only, to locate; run from repo root)
- Find stale version strings:
  - `rg 'schema_version: \"1\\.6\"' .`
  - `rg 'Spec v1\\.7' .`
  - `rg 'ai_task_list_linter_v1_8' .`
  - `rg 'README_ai_task_list_linter_v1_8' .`
- Check mode mentions:
  - `rg 'mode: \"template\"|mode: \"plan\"|mode: \"instantiated\"' .`
- Check linter banner/version:
  - `rg 'LINTER_VERSION|Spec v1\\.9|schema_version 1\\.7' ai_task_list_linter_v1_9.py`

## Edits to perform (content-level)
1) Spec:
   - Header: Spec v1.9; schema_version "1.7".
   - Rule IDs: use R-ATL-NEW-01/02/03 (no PROSE/031 drift). Rule IDs are contract; changing them is a breaking change and must update spec + linter + fixtures in one commit.
   - Remove non-pattern ellipses (forbid `...` in normative prose; allow only in obvious command placeholders like `uv run ...` inside examples).
2) COMMON:
   - Version block: Spec v1.9, schema 1.7, linter v1_9, template v6.0 (the SSOT tuple).
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

## Guardrail (prevent re-drift)
- Add a simple consistency check (script or make target) that:
  - Reads the tuple from COMMON.md.
  - Fails if any other file contains conflicting Spec v / schema_version / linter filename strings.
  - Fails if task-list YAML schema_version differs from COMMON’s schema_version.

## Definition of Done
- `rg 'schema_version: \"1\\.6\"|Spec v1\\.7|ai_task_list_linter_v1_8|README_ai_task_list_linter_v1_8' .` returns nothing (outside archives).
- COMMON.md contains the canonical tuple; no other file contains conflicting version strings.
- Linter banner matches LINTER_VERSION; rule IDs in spec and linter align (NEW-01/02/03).
- Validation suite headers/commands refer to v1.9.
- No non-pattern `...` truncations remain in SSOT docs (spec/COMMON/manuals/template).
