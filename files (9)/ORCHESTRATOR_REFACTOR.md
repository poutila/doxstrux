# Orchestrator Refactor Plan — Introduce `mode: plan` for Clean Lifecycle

Goal: create a three-stage lifecycle that eliminates template-vs-real command friction, tightens governance, and keeps lint deterministic:
- `mode: template` → pristine scaffold, command placeholders allowed.
- `mode: plan` → real commands, output placeholders allowed, no fabricated evidence.
- `mode: instantiated` → real commands + real evidence, no placeholders.

## Why
- Current spec forces template-mode Preconditions to be placeholders, but orchestrator/manuals emit real commands. This causes lint failures on useful “plan” artifacts.
- We need a middle state that requires real commands and governance (runner/search_tool/import hygiene) without forcing real evidence.

## Incremental Refactor Plan
1) Spec (AI_TASK_LIST_SPEC_v1.md)
   - Add `mode: plan` to allowed modes and front-matter validation.
   - Define plan semantics:
     - Commands: MUST be concrete in Preconditions/Global/Phase unlock (no command placeholders).
     - Placeholders allowed only for outputs/evidence.
     - Runner/search_tool/import-hygiene rules apply (same as instantiated).
     - STOP/Baseline/Global evidence may be placeholders; status typically 📋 PLANNED.
   - Update R-ATL-D2 (Preconditions), Global Clean Table, Phase Unlock language to cover plan mode.
   - Clarify lifecycle: template → plan → instantiated.

2) Linter (ai_task_list_linter_v1_8.py)
   - Allow `mode` ∈ {template, plan, instantiated}.
   - Plan-mode enforcement:
     - Preconditions/Global scan: require at least one `$ {search_tool} …` (no `[[PH:SYMBOL_CHECK_COMMAND]]`).
     - Forbid command placeholders in plan mode; allow output placeholders.
     - Apply runner_prefix/uv/import-hygiene checks (like instantiated).
     - Forbid placeholders in YAML/paths/status/naming rule; allow in evidence blocks.
   - Keep instantiated rules unchanged; template rules stay permissive for commands.

3) Template (AI_TASK_LIST_TEMPLATE_v6.md)
   - Add a short “Modes” note describing template/plan/instantiated.
   - Keep template content placeholder-based, but add an example comment showing plan-mode commands in Preconditions/Global (without changing actual placeholders).

4) Orchestrator (PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md)
   - Default output to `mode: "plan"` (not template).
   - Instruction: commands must be real; evidence placeholders OK; no fabrication.
   - Keep Prose Coverage Mapping and governance sweeps; self-check must assert plan-mode rules (no command placeholders, runner/rg compliance).
   - Hard precondition: if any required artifact is missing, stop and ask for the correct path before proceeding. Required artifacts:
     1. **Prose design / requirements**: `[[PH:PROSE_DOC_LABEL]]` (content pasted; e.g., [Target file](./path_to/[[PH:PROSE_DOC_FILENAME]].md)).
     2. **Spec**: [AI_TASK_LIST_SPEC_v1.md](./AI_TASK_LIST_SPEC_v1.md) — Spec v1.6 contract for valid task lists.
     3. **Template**: [AI_TASK_LIST_TEMPLATE_v6.md](./AI_TASK_LIST_TEMPLATE_v6.md) — starting point for new task lists.
     4. **Linter**: [ai_task_list_linter_v1_8.py](./ai_task_list_linter_v1_8.py) — implementation of the spec (assume it will be run after your output).
     5. **AI Assistant Manual**: [AI_ASSISTANT USER_MANUAL.md](./AI_ASSISTANT USER_MANUAL.md).

5) Manuals (AI_ASSISTANT USER_MANUAL.md, USER_MANUAL.md)
   - Update mode guidance: design scaffold = template; normal AI output = plan; human/CI execution = instantiated.
   - Checklists: adjust “design/AI output” to expect mode=plan with real commands, placeholder evidence.
   - Add a note: only template-mode allows command placeholders; plan/instantiated require real commands.

6) README / Index / Description
   - Note the new mode and lifecycle in README_ai_task_list_linter_v1_8.md and INDEX.md.
   - Brief migration blurb in DESCRIPTION.md.

7) Migration for existing task lists
   - For existing “template” artifacts with real commands: switch mode to `plan`.
   - For pure scaffolds: keep `template`.
   - For executed lists: keep `instantiated` and ensure evidence is real.

8) Validation passes
   - Update/extend any linter smoke tests for plan mode (front matter parse + enforcement of real commands/no command placeholders).
   - Re-run linter on: (a) template scaffold, (b) plan artifact (PYDANTIC_SCHEMA_tasks_template.md after mode flip), (c) instantiated sample.
9) Reflection and stage discipline
   - Orchestrator self-check: explicit loop—revise and re-run sweeps if any check fails; only one visible output.
   - Skeleton vs plan vs instantiated:
     - Skeleton: keep as template-only (placeholders everywhere, no real commands).
     - Plan: real commands + governance, evidence placeholders only.
     - Instantiated: real commands + real evidence, no placeholders.
   - Gates: everywhere, use fail-on-match patterns (`! rg …` or `if rg …; then exit 1; fi`); keep this consistent across template examples and plan outputs.
   - Prose Coverage: keep required/recommended mapping; consider flagging critical enumerations (e.g., required paths) for verbatim copy to avoid silent truncation.
   - Runner normalization: ensure all “active” docs (orchestrator/manual/examples/template comments) show only runner-compliant commands; mark legacy commands in external prose as historical if needed.
10) Prompt strategy (avoid drift)
    - Keep one orchestrator prompt with a mode switch:
      - Default path: emit `mode: "plan"` (real commands, placeholder evidence).
      - Template scaffold path: short preamble flag to emit `mode: "template"` with command placeholders.
      - Instantiated helper (optional): minimal add-on to fill evidence into an existing plan, not regenerate structure.
    - Rationale: single SSOT for structure/governance; thin variants reduce sync drift.

## Acceptance Criteria
- Linter cleanly distinguishes template vs plan vs instantiated without false positives.
- Orchestrator-generated “plan” passes lint (no more placeholder-command conflicts).
- Governance (uv/rg/import hygiene/Phase Unlock/STOP evidence structure) remains enforced in plan and instantiated modes.
- Gates in examples and outputs fail on matches (no “always-pass” patterns).
- Docs all describe the same three-mode lifecycle; no contradictory guidance remains (including runner/search_tool usage).
