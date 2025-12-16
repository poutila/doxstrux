# COMMON.md — Shared Framework Definitions

## §Version

**Single source of truth**: `VERSION.yaml`

All tools read the framework version from VERSION.yaml. To bump version, edit that file only.

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

## §Files

| File | Purpose |
|------|---------|
| `VERSION.yaml` | Single source of truth for framework version |
| `AI_TASK_LIST_SPEC.md` | Specification (authoritative contract) |
| `AI_TASK_LIST_TEMPLATE.md` | Template for new task lists |
| `tools/ai_task_list_linter.py` | Linter implementing the spec |
| `PROMPT_AI_TASK_LIST_ORCHESTRATOR.md` | Runtime prompt for prose → task list |
| `MANUAL.md` | Framework manual |
| `PROSE_INPUT_TEMPLATE.md` | Input template for specs |
| `PROMPT_PROSE_INPUT_DISCOVERY.md` | Discovery prompt for gathering project facts |
| `PROMPT_PROSE_INPUT_REVIEW.md` | AI review prompt for semantic validation |
| `tools/prose_input_linter.py` | Input template linter |
| `COMPLETE_VALIDATION.md` | Complete validation pipeline documentation |
