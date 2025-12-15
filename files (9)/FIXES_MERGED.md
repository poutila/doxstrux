# FIXES_MERGED.md — Consolidated Plan to Close Remaining Drifts

Goal: Eliminate iteration drivers by aligning spec/linter/template/manuals, enabling reality-first planning, enforcing coverage, fixing gate patterns, and ensuring a single SSOT.

## Priority Order
1) Mode semantics: allow reality-first planning (add `mode: plan` or relax template-mode command rules).
2) Coverage enforcement: Prose Coverage Mapping validation.
3) Spec as SSOT: remove spec/linter drift.
4) Gates and runner normalization: fail-on-match gates; runner/search_tool-consistent commands.
5) Migration + docs: decision tree, guidance, backward-compatibility.
6) Validation suite: template/plan/instantiated + negatives + doc-sync.
7) Critical enumerations: definition/markers and preservation.

## Work Breakdown (merged from FIX_1 + FIX_2)

### Mode semantics (reality-first planning)
- Spec: add `mode: plan` (Path A, no interim relaxation) with rules:
  - Preconditions/Global/Phase unlock must use real `$ {search_tool} …` commands (no command placeholders); evidence placeholders allowed; runner/search_tool/import-hygiene enforced; placeholders forbidden in YAML/paths/status/naming rule.
  - Lifecycle: template → plan → instantiated.
- Linter: accept mode=plan; enforce real commands in Preconditions/Global/Phase unlock; forbid `[[PH:SYMBOL_CHECK_COMMAND]]`/command placeholders; allow output placeholders; instantiated remains strict.
- Orchestrator: default to plan; self-check enforces plan rules; optional template scaffold flag.
- Manuals/README/INDEX/DESCRIPTION: update mode lifecycle/checklists; only template allows command placeholders; plan/instantiated require real commands.
- Remove interim relaxation: implement plan mode directly to avoid template ambiguity and rework.

### Prose Coverage Mapping enforcement
- Spec: define canonical table: Prose requirement | Source (file/section) | Implemented by task(s).
- Linter: warning in plan/instantiated modes—check header (aliases allowed), Source is anchored (.md or strict section ID), tasks referenced exist.
- Orchestrator/manuals: instruct anchored sources and full task IDs.

### Spec as SSOT
- Update `AI_TASK_LIST_SPEC_v1.md` to match linter behavior/version (schema_version 1.6) or explicitly declare linter as SSOT/spec generated from code—pick one.
- Ensure version labeling consistent (no v1.0.0 vs v1.6 mismatch).
- Docs state spec+linter are authoritative.

### Gates and runner normalization
- Audit/replace any `&& exit 1 ||` gate patterns with fail-on-match (`! rg …` or `if rg …; then exit 1; fi`).
- Audit `$` examples for runner/search_tool compliance (uv run, rg); mark legacy commands as historical if retained.
- Provide search commands to catch bad gates/non-compliant runner examples.

### Migration + user guidance
- Mode decision tree: when to use template vs plan vs instantiated; lifecycle flow.
- Migration guide: flip “template with real commands” to plan; backward-compatibility/deprecation timeline; optional helper script.
- Critical enumerations: define criteria/markers; instruct verbatim copy/count; optional orchestrator/linter hint.
- Linter messaging: suggest `mode: plan` when concrete commands found in template mode.

### Validation suite
- Define/run tests:
  - Template scaffold → expect pass (mode: template).
  - Plan artifact (e.g., PYDANTIC_SCHEMA_tasks after mode flip) → expect pass (mode: plan).
  - Instantiated sample (real evidence) → expect pass with `--require-captured-evidence`.
  - Negative: plan with command placeholders → fail; template with bad gates → fail/warn.
  - Doc-sync check: modes referenced consistently across docs.
- Use runner-consistent command: `uv run python ai_task_list_linter_v1_8.py …`.

### Critical enumerations
- Define “critical enumeration” criteria (completeness required, order may matter, independently verifiable items).
- Markers (e.g., `<!-- CRITICAL_ENUM:label --> … <!-- END_CRITICAL_ENUM -->`); instruct verbatim copy.
- Orchestrator/manual note; consider optional check (count/presence) for plan/instantiated.

## Acceptance Criteria (Definition of Done)
- Mode support: linter/spec/orchestrator/manuals implement and document three-mode lifecycle (or relaxed template) with plan-mode rules enforced; orchestrator defaults to plan and emits real commands + placeholder evidence.
- Coverage: Prose Coverage Mapping guidance present; linter check active (warning/error) with anchored sources and existing tasks.
- SSOT: spec matches linter behavior/version; no conflicting version claims.
- Gates/runner: all examples use fail-on-match gates; runner/search_tool examples compliant or clearly marked legacy.
- Migration: decision tree + migration/deprecation guidance published; linter errors hint at plan mode when applicable.
- Validation: template/plan/instantiated/negative tests defined and executed; doc-sync check passes.
- Critical enumerations: definition/markers documented; orchestrator/manual note included; optional enforcement considered.
- Versioning/communication: version plan documented (e.g., spec v1.7.0/linter v1.9 with schema_version “1.6” unchanged), CHANGELOG entry prepared for breaking changes, user communication (README banner/release notes) outlined, rollback procedure noted.
- Canonical examples: three example files (template/plan/instantiated) created and lint-validated, referenced from spec/docs.
- Real-project validation: migration guide tested on 2–3 real task lists; fresh task list generated from real prose; instantiated mode validated on real data; performance impact checked (<10% overhead target); backward-compat tests on v1.5/v1.6 lists.
- Edge cases: documented stances on mixed-mode (reject), reverse migration (plan→template manual steps), plan-in-CI guidance, schema_version vs spec version distinction.
- SSOT decision: Spec is SSOT; linter implements spec. If spec/linter disagree, fix linter. Document this in spec/README.
- Coverage enforcement: in plan/instantiated modes, missing/empty coverage section ⇒ warning; malformed table/invalid anchors/nonexistent tasks ⇒ error (start as warnings if phased).
- Deprecation timeline: v1.6.1 add plan mode and relax template (warn); v1.7.0 enforce strict template (fail on concrete commands) after ~8-week grace period; schema_version stays 1.6; linter bumps (e.g., v1.9).
- Baseline enforcement: template mode must have Evidence fenced block with [[PH:OUTPUT]] (or canonical placeholder) and Baseline tests fenced block; instantiated mode must enforce $-prefix on Baseline commands/tests and maintain existing non-empty/output checks.
- Phase Gate content: enforce required checklist items in ## STOP — Phase Gate (.phase-N.complete.json exists, Global Clean Table passes, Phase tests pass, Drift ledger current).
- Gate semantics clarity: document in spec/manuals that linter checks presence of gate commands, not shell exit semantics; downgrade “gates must gate” to SHOULD in text unless linter enforcement is added.
- Tracking: use FIXES_STATUS.md to record progress against this plan; FIXES_MERGED.md remains the roadmap (planning document, not status).
- Drift-risk mitigations:
  - Spec/linter lockstep: spec is SSOT; when they diverge, fix linter. Keep version labels in sync (spec v1.7.0/linter v1.9; schema_version stays 1.6).
  - Doc sync: update all framework docs (spec, template, orchestrator, manuals, README/INDEX/DESCRIPTION) to the three-mode model and gate semantics wording.
  - Versioning/communication: include changelog entry, README/release-note banner, deprecation timeline; avoid partial mode flips in migration guidance; decision tree included.
  - Coverage checks: warning for missing/empty; error for malformed/invalid refs; avoid over-flagging benign cases.
  - Gate semantics: be explicit that linter enforces presence, not exit flow, unless shell parsing is added.
  - Canonical examples: lint-validate template/plan/instantiated examples to keep them authoritative.
