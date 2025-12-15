# Fix Plan — Close Remaining Drifts (Template vs Practical Commands, Gates, Alignment)

Goal: Eliminate known friction points (template-mode command placeholders, gate patterns, doc alignment) so command-rich plans lint cleanly and gates actually gate.

## 1) Add `mode: plan` (spec/linter/docs)
- Spec (`AI_TASK_LIST_SPEC_v1.md`): allow `mode: plan`; define rules:
  - Preconditions/Global/Phase unlock MUST use real `$ {search_tool} …` commands (no command placeholders).
  - Evidence/output placeholders allowed; no placeholders in YAML/paths/status/naming rule.
  - Runner/search_tool/import hygiene rules apply (same as instantiated).
  - Lifecycle: template → plan → instantiated.
- Linter (`ai_task_list_linter_v1_8.py`):
  - Accept `plan` in front matter.
  - Plan-mode enforcement: require real `$ {search_tool} …` in Preconditions/Global; forbid `[[PH:SYMBOL_CHECK_COMMAND]]`/command placeholders; apply runner/uv/import-hygiene checks; allow output placeholders in evidence blocks.
- Template (`AI_TASK_LIST_TEMPLATE_v6.md`):
  - Add a short “Modes” note; keep placeholders, but include a comment showing plan-mode command examples.
- Orchestrator (`PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md`):
  - Default output to `mode: "plan"`; explicitly require real commands, placeholder evidence; self-check enforces plan rules.
- Manuals (`AI_ASSISTANT USER_MANUAL.md`, `USER_MANUAL.md`, `README_ai_task_list_linter_v1_8.md`, `DESCRIPTION.md`, `INDEX.md`):
  - Update mode guidance and checklists to template/plan/instantiated; note that only template allows command placeholders.

## 2) Gate patterns (fail on match everywhere)
- Ensure all gate examples use fail-on-match (`! rg …` or `if rg …; then exit 1; fi`):
  - Template (already fixed for standard patterns).
  - Orchestrator and manuals: verify any gate snippets use fail-on-match (no `&& exit 1 || echo`).
  - Update any lingering examples in evaluation/fix guides as needed.

## 3) Clean Table/Preconditions placeholders vs. real commands
- Until plan mode ships, note in docs: template mode requires placeholders; plan mode resolves this tension. When plan mode is live, regenerate plan lists or flip existing “template with real commands” to `mode: plan`.

## 4) Prose Coverage and critical enumerations
- Keep Prose Coverage Mapping recommended; for critical lists (e.g., security paths), instruct assistants to copy them verbatim or mark as such to avoid truncation. Consider adding a doc note to highlight this in orchestrator/manuals.

## 5) Runner normalization
- Ensure active framework docs show only runner-compliant commands (uv, rg). Mark any legacy commands in external prose as historical/non-authoritative if needed.

## 6) Validation passes
- After changes: run linter on (a) template scaffold, (b) plan artifact (e.g., PYDANTIC_SCHEMA_tasks_template.md after mode flip), (c) instantiated sample. Verify gates/gov checks remain enforced.

## Expected outcome
- Command-rich plans lint cleanly under `mode: plan`.
- Gates fail on matches; no always-pass patterns remain.
- Docs and orchestrator align on three-mode lifecycle; no contradictory guidance.

## Required additions (from feedback)
- Mode selection decision tree (spec/orchestrator/manuals): when to use template vs plan vs instantiated; include lifecycle flow.
- Migration guide and backward-compatibility plan for existing “template with real commands” docs; deprecation timeline.
- Critical enumerations: define markers and criteria; instruct verbatim copy/count; add notes to orchestrator/manuals; consider optional linter/orchestrator check.
- Validation test suite: specify inputs/commands/expected outcomes for template, plan, instantiated, and negative cases.
- Linter error messaging: suggest `mode: plan` when concrete commands appear in template mode.
- Gate audit: ensure all examples use fail-on-match; include a search command to find bad patterns.
- Runner normalization: audit examples; decide normalize vs flag; document behavior.
- Doc sync: keep spec as SSOT for mode definitions; ensure all framework docs reference it consistently.

## Optimal fix order (minimize churn)
1) Spec + linter core: add `mode: plan`, define rules; implement plan-mode enforcement and error messaging.
2) Template + orchestrator: add modes note, switch orchestrator default to plan, enforce plan rules in self-check.
3) Manuals/README/DESCRIPTION/INDEX: update mode guidance and checklists; note critical enumerations; runner normalization stance.
4) Gates and runner normalization audit: fix any lingering always-pass gate patterns and non-runner-compliant examples across docs.
5) Migration guidance: publish decision tree, migration guide/deprecation timeline; backward-compatibility notes.
6) Validation suite: define and run template/plan/instantiated/negative tests; add doc-sync check.
7) Critical enumerations: add marker definition and orchestrator/manual note; optional warning in linter/orchestrator.

## Acceptance Criteria (definition of done)
- Spec/linter accept and enforce `mode: plan` per defined rules; template/plan/instantiated behaviors differentiated.
- Orchestrator defaults to plan, emits real commands + placeholder evidence, and self-check enforces plan rules.
- All framework docs (template, orchestrator, manuals, README, DESCRIPTION, INDEX) present a consistent three-mode lifecycle and mode decision guidance.
- Gate examples across docs use fail-on-match patterns only; runner examples are normalization-compliant or clearly marked legacy.
- Migration guide and deprecation plan published; decision tree included.
- Validation suite defined and executed for template, plan, instantiated, and negative cases; doc-sync check passes.
- Critical enumeration guidance present (definition + markers) and referenced by orchestrator/manual; optional checks considered.
