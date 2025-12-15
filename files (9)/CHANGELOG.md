# Changelog

## [1.9] - 2025-xx-xx
- Spec v1.7 (schema_version stays 1.6) adds plan mode (real commands + evidence placeholders).
- Linter v1.9 (code filename unchanged) accepts plan mode; enforces template/plan baseline evidence/[[PH:OUTPUT]] and Baseline tests block; enforces Phase Gate checklist; extends $-prefix to Baseline; adds Prose Coverage Mapping check (plan/instantiated).
- Documentation updated to three-mode lifecycle; migration guide and validation suite added; canonical examples lint-clean (template/plan/instantiated).
- Gate semantics clarified: linter enforces presence; fail-on-match patterns are recommended (process-level).

## [1.8] - previous
- Closed comment-compliance holes (import hygiene, Phase Unlock scans, uv commands) by requiring $ command lines.
- Enforced .phase-N.complete.json suffix; required STOP evidence fenced block; tightened status/checklists.
- Added Baseline tests enforcement.
