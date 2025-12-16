
## [v1.9] - Alignment and new enforcement
- Spec v1.9 (schema_version 1.7), three modes (template/plan/instantiated) now aligned across spec/COMMON/manuals/README/orchestrator/template.
- Linter v1.9 adds NEW-01 (unique Task IDs), NEW-02 (Prose Coverage Mapping references must resolve to existing unique tasks; Implemented-by column required; ranges forward/same prefix), NEW-03 (Global Clean Table required in plan/instantiated).
- Updated canonical examples (plan/instantiated) and negatives; validation suite references NEW-02; canary baseline recorded.
- Deprecated schema_version 1.6 / Spec v1.7 references removed from framework docs/examples.

# Changelog

## [1.9] - 2025-xx-xx
- Spec v1.9 (schema_version 1.7) supports template/plan/instantiated; plan allows evidence placeholders.
- Linter v1.9 (code filename unchanged) accepts plan mode; enforces template/plan baseline evidence/[[PH:OUTPUT]] and Baseline tests block; enforces Phase Gate checklist; extends $-prefix to Baseline; adds Prose Coverage Mapping check (plan/instantiated).
- Documentation updated to three-mode lifecycle; migration guide and validation suite added; canonical examples lint-clean (template/plan/instantiated).
- Gate semantics clarified: linter enforces presence; fail-on-match patterns are recommended (process-level).

## [1.8] - previous
- Closed comment-compliance holes (import hygiene, Phase Unlock scans, uv commands) by requiring $ command lines.
- Enforced .phase-N.complete.json suffix; required STOP evidence fenced block; tightened status/checklists.
- Added Baseline tests enforcement.
