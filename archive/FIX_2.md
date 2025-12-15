# Fix Plan 2 — Close Remaining Tool/Spec Drift and Coverage Gaps

Goal: Remove iteration drivers by aligning spec/linter/template/manuals, enabling reality-first planning, enforcing coverage, and eliminating gate/spec drift.

## Priority Order
1) Mode semantics: allow reality-first planning (template/plan)
2) Coverage enforcement: Prose Coverage Mapping check
3) Spec as SSOT: eliminate spec/linter drift
4) Gates and runner normalization: fail-on-match everywhere; consistent commands
5) Migration + docs: decision tree, guidance, backward-compatibility
6) Validation suite: template/plan/instantiated + negatives + doc-sync

## Work Breakdown

### 1) Mode semantics (reality-first planning)
- Decide/implement `mode: plan` (preferred) or relax template mode:
  - Spec: add plan mode; define rules (real commands required; evidence placeholders allowed; runner/search_tool/import hygiene enforced; no command placeholders; placeholders only in evidence).
  - Linter: accept mode=plan; enforce real `$ {search_tool} …` in Preconditions/Global/Phase unlock; forbid command placeholders; allow output placeholders; keep instantiated strict.
  - Orchestrator: default to plan; self-check for plan rules; template scaffold optional flag.
  - Manuals/README/INDEX/DESCRIPTION: update mode lifecycle and checklists; only template allows command placeholders; plan/instantiated require real commands.
  - If not adding plan: relax template-mode checks to accept real commands in Preconditions/Global in addition to placeholders (temporary).

### 2) Prose Coverage Mapping enforcement
- Spec: define a canonical “## Prose Coverage Mapping” table (columns: Prose requirement | Source (file/section) | Implemented by task(s)).
- Linter: optional warning/error when table exists:
  - Require header row (allow minimal aliases).
  - Source must reference `.md` or strict section ID format.
  - Tasks listed must exist in the document.
- Orchestrator/manuals: instruct using file/section anchors (not loose labels) and full task IDs.

### 3) Spec as SSOT (eliminate drift)
- Update `AI_TASK_LIST_SPEC_v1.md` to match linter behavior (schema_version 1.6, current rules), or state explicitly that spec is generated from linter (pick one SSOT).
- Ensure spec version labeling matches code (no v1.0.0 vs v1.6 mismatch).
- Add a note in docs: spec/linter are authoritative; template/manuals/orchestrator derive from them.

### 4) Gates and runner normalization
- Gate patterns: audit all framework docs for `&& exit 1 ||` patterns; replace with fail-on-match (`! rg …` or `if rg …; then exit 1; fi`).
- Runner normalization: audit `$` examples; replace bare python/pip/grep with runner/search_tool compliant commands (uv run, rg) or mark legacy as historical.
- Provide a search command to catch bad gate patterns and non-compliant runner commands.

### 5) Migration + user guidance
- Mode decision tree: when to use template vs plan vs instantiated; include lifecycle flow.
- Migration guide: flip “template with real commands” to plan; backward-compatibility/deprecation timeline; optional helper script.
- Critical enumerations: define criteria and markers for verbatim copy; instruct assistants to preserve; optional orchestrator/linter hint.
- Linter messaging: suggest `mode: plan` when concrete commands are found in template mode.

### 6) Validation suite
- Define and run tests:
  - Template scaffold → expect pass (mode: template).
  - Plan artifact (e.g., PYDANTIC_SCHEMA_tasks after mode flip) → expect pass (mode: plan).
  - Instantiated sample with real evidence → expect pass (mode: instantiated, with --require-captured-evidence).
  - Negative cases: plan with command placeholders (fail); template with bad gates (fail/warn).
  - Doc-sync check: ensure all framework docs mention modes consistently.
- Use runner-consistent command (`uv run python ai_task_list_linter_v1_8.py …`).

## Acceptance Criteria (DoD)
- Mode support: linter/spec/orchestrator/manuals implement and document three-mode lifecycle (or relaxed template) with plan-mode rules enforced.
- Coverage: Prose Coverage Mapping guidance present; linter check active (warning or error) with canonical header and anchored sources/tasks.
- SSOT: spec matches linter behavior/version; no conflicting version claims.
- Gates/runner: all examples use fail-on-match gates; runner/search_tool examples are compliant or explicitly marked legacy.
- Migration: decision tree + migration/deprecation guidance published; linter errors hint at plan mode when applicable.
- Validation: template/plan/instantiated/negative tests defined and executed; doc-sync check passes.
- Critical enumerations: definition/markers documented; orchestrator/manual note included (optional check considered).
