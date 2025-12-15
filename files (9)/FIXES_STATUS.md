# FIXES_STATUS.md — Execution Tracker for FIXES_MERGED Plan

## Legend
- [ ] Not started
- [~] In progress
- [x] Completed

## Core Work Items
- [ ] Spec: add `mode: plan` (spec v1.7.0), clarify SSOT (spec wins; fix linter on drift), coverage warning rules, gate semantics (presence enforced; exit semantics process-level).
- [ ] Linter: add `mode: plan` (v1.9), enforce plan rules (real commands, no command placeholders; allow output placeholders), coverage mapping warning/error behavior, $-prefix Baseline checks, Phase Gate checklist enforcement, baseline template checks, improved messages (suggest plan when template has real commands).
- [ ] Template: add modes note; keep placeholders; include plan-mode examples in comments.
- [ ] Orchestrator: default output to plan; stop if required artifacts missing; self-check plan rules.
- [ ] Manuals/README/INDEX/DESCRIPTION: update to three-mode lifecycle; coverage guidance; gate semantics clarification; runner normalization notes.
- [ ] Canonical examples: create and lint-validate example_template.md, example_plan.md, example_instantiated.md.
- [ ] Migration guide/decision tree: template vs plan vs instantiated; deprecation timeline (v1.6.1 warn, v1.7.0 enforce).
- [ ] Validation suite: template/plan/instantiated/negative tests; doc-sync check; real-project validation; perf/backward-compat checks; changelog.

## Notes
- Current framework: spec v1.6, linter v1.8, no plan mode implemented yet.
- FIXES_MERGED.md is the roadmap; this file tracks execution status.
