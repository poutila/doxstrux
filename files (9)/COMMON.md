# COMMON.md — Shared Framework Definitions

## §Version Metadata
- Spec: v1.9 (schema_version: "1.7")
- Linter: v1.9 (`ai_task_list_linter_v1_9.py`)
- Template: v6.0

## §SSOT Hierarchy
1) Spec (authoritative contract)
2) Linter (implements the spec; if spec and linter diverge, fix the linter)
3) Template, manuals, orchestrator
4) Prose (lowest; must not contradict 1–3)

## §Mode Definitions
- `template`: placeholders allowed (commands and evidence); used for generic scaffolds.
- `plan`: real commands required; evidence/output placeholders allowed; runner/search_tool/import-hygiene rules apply.
- `instantiated`: no placeholders anywhere; real evidence required.
- Lifecycle: template → plan → instantiated.
