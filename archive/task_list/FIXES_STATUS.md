# FIXES_STATUS.md — Execution Tracker for FIXES_MERGED Plan

## Legend
- [ ] Not started
- [~] In progress
- [x] Completed

## Core Work Items
- [x] Spec: add `mode: plan` (spec v1.7.0), clarify SSOT (spec wins; fix linter on drift), coverage behavior, gate semantics (presence enforced; exit semantics process-level).
- [x] Linter: add `mode: plan` (v1.9), enforce plan rules (real commands, no command placeholders; allow output placeholders), coverage mapping check, $-prefix Baseline checks, Phase Gate checklist enforcement, baseline template checks, improved messages (suggest plan when template has real commands).
- [x] Template: add modes note; keep placeholders; include plan-mode examples in comments.
- [x] Orchestrator: default output to plan; stop if required artifacts missing; self-check plan rules.
- [x] Manuals/README/INDEX/DESCRIPTION: update to three-mode lifecycle; coverage guidance; gate semantics clarification; runner normalization notes.
- [x] Canonical examples: create and lint-validate example_template.md, example_plan.md, example_instantiated.md.
- [x] Migration guide/decision tree: template vs plan vs instantiated; deprecation timeline (v1.6.1 warn, v1.7.0 enforce).
- [x] Validation suite: template/plan/instantiated/negative tests; doc-sync check; real-project validation; perf/backward-compat checks; changelog.

## Reflection / Notes
- We should stage the work into PR-sized steps to reduce risk:
  1) Core rules (spec/linter plan mode, baseline/Phase Gate/coverage, version/changelog).
  2) Framework docs (template, orchestrator, manuals, README/INDEX/DESCRIPTION).
  3) Examples + migration guide/decision tree + deprecation timeline.
  4) Validation suite (tests, doc-sync, real-project sanity, perf/backcompat).
- Be explicit in docs that linter enforces presence, not shell exit semantics (gate failure patterns are process-level unless we add parsing).
- Coverage mapping: warn on missing/empty; error on malformed/invalid anchors/nonexistent tasks—avoid over-flagging benign cases.
- Canonical examples must be lint-validated to stay authoritative.

## Notes
- Current framework: spec v1.7 (plan mode added), linter v1.9 (code file name unchanged); docs/migration/examples updated; validation/changelog still pending.
- FIXES_MERGED.md is the roadmap; this file tracks execution status.
