# TEMPLATE_DROP.md — Plan to Remove Template Mode (No Backward Compat)

Goal: Remove `mode: template` from the framework, bump schema_version, and align all artifacts and fixtures to a two-mode lifecycle: plan (real commands, evidence placeholders) and instantiated (real evidence, no placeholders).

## Scope and SSOT Order
1) Spec (authoritative contract): remove template mode, define valid modes as plan/instantiated, bump schema_version.
2) Linter: enforce new schema/version and mode set; remove template-specific rules; update file/version identifiers.
3) COMMON: update version metadata, mode definitions, runner/import/gate rules to two-mode contract.
4) Docs/Template/README/Manuals/INDEX/Orchestrator: remove template-mode references; update usage examples and commands.
5) Fixtures/Validation: drop template fixtures; update positives/negatives/suite; update baselines/canaries.

## Versioning
- Spec: bump to v2.0 (breaking: template removed).
- schema_version: bump to 1.8 (breaking YAML change: mode set shrinks).
- Linter: release `ai_task_list_linter_v2_0.py` with `LINTER_VERSION = "2.0.0"`; update all references to v2_0.

## Linter Changes (ai_task_list_linter_v2_0.py)
- Front matter: `schema_version` must be "1.8"; `mode` must be `plan` or `instantiated` (case-sensitive). Remove `template` from validation.
- Evidence rules (R-ATL-022): plan allows evidence placeholders; instantiated forbids placeholders and requires real output (at least one $ command and one non-placeholder line; allow explicit `# no output` marker).
- Remove template-mode branches:
  - Baseline Snapshot and Baseline tests: drop template placeholder checks.
  - Phase Unlock Artifact: drop template-specific fenced-block and placeholder requirements.
  - Global Clean Table: drop template placeholder requirements; keep instantiated rules.
  - STOP evidence: drop template placeholder requirements.
  - Preconditions (R-ATL-D2): remove template placeholder allowance; plan must use real search_tool command; instantiated same.
  - Clean Table/STOP checklists: remove template-only placeholder allowances.
- R-ATL-075 scope: keep existing behavior; ensure it applies to plan/instantiated only.
- New filenames/args: argparse prog updated to `ai_task_list_linter_v2_0.py`; `--version` prints 2.0.0.

## Spec Changes (AI_TASK_LIST_SPEC_v1.md → v2.0 content)
- Update header: Spec v2.0; schema_version "1.8".
- Mode definition: valid modes = plan | instantiated. Template mode removed.
- Front matter examples: schema_version "1.8"; mode plan/instantiated only.
- Remove template-mode allowances in Evidence, Baseline, STOP, Global Clean Table, Phase Unlock, Preconditions.
- Coverage mapping rules unchanged; clarify applicable to plan/instantiated.
- Minimal compliance summary: update schema_version, mode set, version IDs.
- Append explicit note: template mode removed in v2.0; use plan for scaffolds.

## COMMON Updates
- Version metadata: Spec v2.0, Linter v2.0, schema_version 1.8, Template v6 note removed or marked legacy.
- Mode definitions: only plan and instantiated; remove template bullets.
- Runner/import/gate/placeholder/evidence rules: remove template allowances; plan/instantiated only.

## Docs/Orchestrator/Manuals/Index
- INDEX: update Spec v2.0, Linter v2.0, remove template references.
- USER_MANUAL, AI_ASSISTANT USER_MANUAL: adjust mode guidance (plan as scaffold; instantiated for real evidence); remove template instructions; update commands to v2_0.
- PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1: set target mode=plan output; references to spec v2.0/schema 1.8; linter v2_0.
- README_ai_task_list_linter_v1_9.md → rename/update to README_ai_task_list_linter_v2_0.md with new versions.
- Template file: either deprecate AI_TASK_LIST_TEMPLATE_v6.md or replace its YAML front matter with schema_version 1.8 and mode plan scaffold; remove template-specific placeholder requirements in comments.

## Fixtures/Validation
- Remove template fixtures; keep/create plan/instantiated examples.
- Update negatives/positives to schema_version 1.8 and modes plan/instantiated.
- VALIDATION_SUITE: update commands to use v2_0 linter; remove template category; ensure plan/instantiated coverage.
- Baseline/canaries: rerun baselines with v2_0; adjust manifest to plan/instantiated only.

## Migration/Compatibility Notes
- Breaking change: template mode dropped; schema_version bumped to 1.8. Older template-mode task lists will fail until migrated to plan or instantiated.
- Provide a short migration note in CHANGELOG and README.

## Work Plan
1) Code: copy v1_9 → ai_task_list_linter_v2_0.py; implement schema/version/mode changes; drop template branches; update prog/--version.
2) Spec/COMMON: update versions, mode set, remove template allowances; add removal note.
3) Docs: rename/update README to v2_0; update INDEX, USER_MANUAL, AI_ASSISTANT manual, orchestrator prompt; adjust template file/YAML comment.
4) Fixtures/Validation: update all fixtures to schema_version 1.8, modes plan/instantiated; drop template fixtures; update VALIDATION_SUITE commands; rerun baselines/canaries with v2_0.
5) Final pass: search/replace leftover “template mode” references; ensure no commands reference v1_9; update CHANGELOG with breaking change entry.
