# FIXES_STATUS.md — Framework Cleanup Tracker

Status snapshot after COMMON.md integration and plan-mode rollout. All errors are loud; remaining items are explicitly listed.

## Done
- COMMON.md added as SSOT (Spec v1.7, schema_version "1.6", plan mode lifecycle).
- Spec trimmed to a single normative contract (v1.7); historical content removed.
- Linter v1.9 rules implemented (plan mode, coverage check, Baseline enforcement, Phase Gate checklists).
- Orchestrator/manuals/docs synced to plan-mode default and COMMON.md references.
- Canonical examples (template/plan/instantiated) validated via `VALIDATION_SUITE.md`.
- CHANGELOG and MIGRATION_GUIDE published for v1.9/plan-mode adoption.

## Open (track explicitly)
- Spec is a reference document, not a lint target; keep it that way (no YAML front matter).
- Keep SSOT names consistent (e.g., AI_ASSISTANT USER_MANUAL.md) when adding new docs.
- When adding new governance rules, update COMMON.md first, then spec/linter/template/manuals in one pass.
- Maintain a clean negative-fixture set for regression (canonical_examples/negatives: plan_preconditions_placeholder, plan_missing_coverage_mapping, template_missing_clean_table_placeholder).

## Next Validation Pass
- Run `VALIDATION_SUITE.md` commands (positive and negative cases) after any rule change. Last run: PASS for template/plan/instantiated positives; negatives for coverage, Clean Table placeholder, and plan Preconditions placeholder all fail as expected (R-ATL-PROSE / R-ATL-060 / R-ATL-D2).
- Re-lint `canonical_examples/*.md` for template/plan/instantiated after edits to linter/spec/template (PASS as of last run).
