# IMPLEMENTING_COMMON.md — Plan to Introduce COMMON.md (Drift Reduction)

Goal: Eliminate cross-doc drift (versions, modes, SSOT, runner/import/gate/placeholder/evidence rules) by introducing a single shared COMMON.md referenced by all framework docs. Keep KISS/YAGNI: extract only high-overlap items; leave workflows/examples/checklists in-place.

## Scope (what to extract)
- Version metadata: Spec v1.7, Linter v1.9 (code filename unchanged), Template v6, schema_version "1.6".
- SSOT hierarchy: Spec (authoritative), linter implements spec (fix linter on divergence), then template/manual/orchestrator, then prose.
- Mode definitions: template (placeholders), plan (real commands, evidence placeholders), instantiated (no placeholders); lifecycle.
- Runner rules: required/forbidden patterns for runner=uv; runner_prefix usage.
- Import hygiene (Python/uv): required `$ rg 'from \.\.'` and `$ rg 'import \*'` checks.
- Gate patterns: recommended fail-on-match; anti-patterns.
- Placeholder protocol: [[PH:...]] format; pre-flight regex.
- Status values: 📋 PLANNED | ⏳ IN PROGRESS | ✅ COMPLETE | ❌ BLOCKED.
- Evidence requirements: fenced blocks, $-prefix, non-empty output, captured headers optional flag.

## Out of scope (keep local)
- Workflows (human vs AI vs orchestrator specifics).
- Examples and checklists (contextual).
- Release notes/changelog (temporal).
- Error messages (linter-specific).

## Files to update with references
- AI_TASK_LIST_SPEC_v1.md
- ai_task_list_linter_v1_8.py (doc/header comment if present)
- AI_TASK_LIST_TEMPLATE_v6.md
- PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
- USER_MANUAL.md
- AI_ASSISTANT USER_MANUAL.md
- README_ai_task_list_linter_v1_8.md
- DESCRIPTION.md
- INDEX.md
- MIGRATION_GUIDE.md
- VALIDATION_SUITE.md
- CHANGELOG.md (link to COMMON.md for versions)

## Steps
1) Create COMMON.md
   - Sections: §Version Metadata; §SSOT Hierarchy; §Mode Definitions; §Runner Rules; §Import Hygiene; §Gate Patterns; §Placeholder Protocol; §Status Values; §Evidence Requirements.
   - Keep concise; no workflows/examples.

2) Insert references
   - Add invisible comments near relevant sections: `<!-- See COMMON.md §Mode Definitions -->`, etc.
   - Ensure top-level docs point to COMMON.md for versions/SSOT/modes; remove duplicated phrasing where safe.

3) Normalize wording
   - Remove conflicting SSOT/mode/coverage statements now covered by COMMON.md.
   - Keep docs brief: “Modes: see COMMON.md §Mode Definitions.”

4) Validation
   - Doc-sync check: grep for version strings and mode lists to ensure only COMMON.md holds canonical text.
   - Lint examples remain unaffected; ensure references don’t alter linter behavior.

## Reference Format Specification
- Use HTML comments to indicate canonical source, e.g., `<!-- See COMMON.md §Mode Definitions -->` above mode descriptions.
- Place comments directly above the section they refer to in each doc.
- Reference sections: §Version Metadata, §SSOT Hierarchy, §Mode Definitions, §Runner Rules, §Import Hygiene, §Gate Patterns, §Placeholder Protocol, §Status Values, §Evidence Requirements.

## Validation Checks (Step 4 — Detailed Commands)
- Versions: `rg 'Spec v1' .` and `rg 'schema_version' .` — ensure only COMMON.md has authoritative values.
- Modes: `rg 'mode: \"' AI_TASK_LIST_* PROMPT_* USER_MANUAL.md 'AI_ASSISTANT USER_MANUAL.md'` — confirm template/plan/instantiated lists match COMMON.md.
- SSOT: check SSOT wording in spec/manual/orchestrator references COMMON.md.
- Runner/import hygiene: ensure examples use uv/rg as per COMMON.md.
- Gate patterns: search for `&& exit 1 ||` anti-patterns; ensure guidance matches COMMON.md.
- Coverage: ensure Prose Coverage Mapping requirement matches COMMON.md wording.

## Content Removal Guidelines
- Remove duplicated canonical definitions (versions, SSOT, modes, runner/import/gate/placeholder/evidence/status) from individual docs; replace with a reference comment plus a brief pointer if needed.
- Keep audience-specific workflows/checklists/examples intact.
- Do not remove linter-specific behavior descriptions or release notes.

## COMMON.md Structure Specification
- Header with Version Metadata (Spec v1.7, Linter v1.9, Template v6, schema_version "1.6").
- Sections: SSOT Hierarchy; Mode Definitions (template/plan/instantiated + lifecycle); Runner Rules (uv requirements/forbidden); Import Hygiene; Gate Patterns (recommended + anti-patterns); Placeholder Protocol (format + pre-flight); Status Values; Evidence Requirements (fenced, $, non-empty, captured headers optional).
- Footer: note that COMMON.md is the single source for the above; other docs reference it.

## Execution order (1 day target, with rollback)
- Hour 1: Re-read COMMON.md spec and confirm version metadata; draft/adjust COMMON.md with the 9 high-overlap items.
- Hour 2: Add references to spec/template/orchestrator/manuals/README/INDEX/DESCRIPTION.
- Hour 3: Update migration/validation/changelog with COMMON.md version reference.
- Hour 4: Run doc-sync checks (grep versions/modes) to confirm single-source; quick manual scan for SSOT/mode consistency.
- Hour 5: Run `VALIDATION_SUITE.md` positives (template/plan/instantiated) and fix fast blockers.
- Hour 6: Run `VALIDATION_SUITE.md` negatives (regression fixtures) and fix any surprises.
- Hour 7-8: Re-run full `VALIDATION_SUITE.md`; fix residual wording conflicts; commit.
- Rollback plan: work on a branch; if validation fails, revert the branch; keep backups of pre-COMMON.md docs until validation passes.

## Acceptance Criteria
- COMMON.md exists with the agreed shared sections.
- All listed docs reference COMMON.md for versions, SSOT, modes, runner/import/gate/placeholder/evidence rules.
- No conflicting SSOT/mode/coverage statements remain in individual docs.
- Version metadata appears once (COMMON.md) and is referenced elsewhere.
- Doc-sync check passes (no stray version/mode lists outside COMMON.md).
