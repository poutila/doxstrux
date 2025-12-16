# VERSION_NORMALIZATION.md — Plan to Normalize Version Metadata

Goal: One consistent version story across all framework artifacts.
SSOT policy (SSOT set):
- COMMON.md carries the canonical human-readable version tuple.
- AI_TASK_LIST_SPEC_v1.md header is an authoritative contract surface.
- ai_task_list_linter_v1_9.py (LINTER_VERSION + required schema_version enforcement) is an authoritative enforcement surface.
These three MUST match. All other docs MUST either reference COMMON.md (§Version Metadata) or stay silent on concrete numbers.

COMMON.md parsing (no guessing):
- Find section with heading exactly `## §Version Metadata`.
- Read lines until the next `##` heading.
- Parse the tuple from lines matching:
  - `Spec: v(\d+\.\d+)`
  - `schema_version: \"(\d+\.\d+)\"`
  - `Linter: ai_task_list_linter_v(\d+)_(\d+)\.py`
  - `Template: v(\d+\.\d+)`
Target tuple in COMMON.md:
- Spec: v1.9
- schema_version: "1.7"
- Linter: ai_task_list_linter_v1_9.py (LINTER_VERSION = 1.9.0)
- Template: v6.0
- Modes: template / plan / instantiated

## Scope (what to fix)
- AI_TASK_LIST_SPEC_v1.md: header/banner, placeholders spelled out (no truncation `...` in normative text; see ellipsis policy below).
- COMMON.md: Version metadata (the SSOT tuple), mode definitions, runner/import/evidence rules.
- Linter: ai_task_list_linter_v1_9.py banner text; ensure version string matches LINTER_VERSION; rule IDs consistent with spec.
- README_ai_task_list_linter_v1_9.md: Replace concrete version strings with “See COMMON.md §Version Metadata” (keep file name references).
- Manuals: USER_MANUAL.md, AI_ASSISTANT USER_MANUAL.md, PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md — replace concrete version strings with “See COMMON.md §Version Metadata”.
- Template: AI_TASK_LIST_TEMPLATE_v6.md — keep schema_version: "1.7" in YAML; elsewhere refer to COMMON for versions.
- Validation suite: VALIDATION_SUITE.md — refer to COMMON for versions; commands point to ai_task_list_linter_v1_9.py.
- Index: INDEX.md — refer to COMMON for versions; keep paths accurate.
- CHANGELOG: ensure v1.9 entry matches tuple.
- Optional: Archived docs (task_list_archive, etc.) — mark as legacy or leave untouched; do not confuse SSOT.

## Search/replace commands (read-only, to locate; run from repo root)
- Find stale version strings:
  - `rg 'schema_version: \"1\\.6\"' .`
  - `rg 'Spec v1\\.7' .`
  - `rg 'ai_task_list_linter_v1_8' .`
  - `rg 'README_ai_task_list_linter_v1_8' .`
- Find version references in prose (beyond exact strings):
  - Old versions only: `rg '(?i)\\bversion\\s+1\\.(6|8)\\b|\\bv1\\.(6|8)\\b|\\bschema\\s+1\\.(6|8)\\b' . --glob '!*archive*' --glob '!task_list_archive/**' --glob '!work_folder/**'`
  - Current version in non-SSOT files (should be absent): `rg '\\bv1\\.7\\b|schema.*1\\.7' . --glob '!COMMON.md' --glob '!AI_TASK_LIST_SPEC_v1.md' --glob '!ai_task_list_linter_v1_9.py' --glob '!*archive*' --glob '!task_list_archive/**' --glob '!work_folder/**'`
- Find linter filename references in docs:
  - `rg 'ai_task_list_linter_v1_[0-9]+' . --glob '!*archive*' --glob '!task_list_archive/**' --glob '!work_folder/**'`
- Check mode mentions:
  - `rg 'mode: \"template\"|mode: \"plan\"|mode: \"instantiated\"' .`
- Check linter banner/version:
  - `rg 'LINTER_VERSION|Spec v1\\.9|schema_version 1\\.7' ai_task_list_linter_v1_9.py`
- Check LINTER_VERSION format + schema enforcement in code:
  - `rg 'LINTER_VERSION\\s*=\\s*['\\\"]\\d+\\.\\d+' ai_task_list_linter_*.py`
  - `rg 'schema_version.*==.*['\\\"]1\\.\\d+' ai_task_list_linter_*.py`
- Check cross-references that may embed versions:
  - `rg 'See.*Spec v|See.*schema_version' . --glob '!*archive*' --glob '!task_list_archive/**' --glob '!work_folder/**'`

## Edits to perform (content-level)
1) Spec:
   - Header: Spec v1.9; schema_version "1.7".
   - Rule IDs: NO renames in this plan. Spec and linter must reference the same IDs. If rule ID renames are desired, do them in a separate plan (e.g., RULE_ID_STABILIZATION.md) as an explicit breaking contract migration.
   - Ellipsis policy (deterministic):
     - Normative prose = any line outside fenced code blocks in SSOT docs (COMMON.md, AI_TASK_LIST_SPEC_v1.md, USER_MANUAL.md, AI_ASSISTANT USER_MANUAL.md, AI_TASK_LIST_TEMPLATE_v6.md).
     - Forbidden: `...` anywhere in normative prose.
     - Allowed inside fenced code blocks only (language {bash, sh}), and only on lines matching: `^(\\$\\s*)?(uv run|rg)\\b.*\\.\\.\\.` (example/command placeholders). Intentional: only `uv run`/`rg` placeholders are allowed; all other commands must be explicit.
2) COMMON:
   - Version block: Spec v1.9, schema 1.7, linter v1_9, template v6.0 (the SSOT tuple).
   - Mode table: template/plan/instantiated, placeholders spelled out.
3) Linter:
   - Banner text: Spec v1.9; schema_version 1.7; three modes.
   - LINTER_VERSION = 1.9.0; ensure docstring reflects it.
   - Filename/version consistency: ai_task_list_linter_v<MAJOR>_<MINOR>.py MUST match LINTER_VERSION major.minor (e.g., 1.9.x → v1_9).
4) README_ai_task_list_linter_v1_9.md:
   - Replace concrete version strings with “See COMMON.md §Version Metadata”; keep file name references. “File name references” = literal filenames/links (e.g., `ai_task_list_linter_v1_9.py`). Update any older filenames (e.g., v1_8) to current.
5) Manuals (USER_MANUAL.md, AI_ASSISTANT USER_MANUAL.md, PROMPT_ORCHESTRATOR):
   - Replace concrete version strings with “See COMMON.md §Version Metadata”; keep schema_version examples at "1.7".
6) Template:
   - Keep schema_version: "1.7" in front matter; elsewhere, reference COMMON for versions.
7) VALIDATION_SUITE.md:
   - Refer to COMMON for version tuple; commands point to ai_task_list_linter_v1_9.py.
8) INDEX.md:
   - Refer to COMMON for version tuple; keep paths accurate.
9) CHANGELOG:
   - Ensure v1.9 entry matches tuple.

## Guardrail (prevent re-drift)
- Add a simple consistency check (script or make target), e.g., `tools/check_version_consistency.py`, that:
  - Reads the tuple from COMMON.md (per parsing rules above).
  - Excludes: `**/archive/**`, `task_list_archive/**`, `work_folder/**`, `.git/**`.
  - Allowed files to contain concrete version literals outside YAML:
    - COMMON.md
    - AI_TASK_LIST_SPEC_v1.md
    - ai_task_list_linter_v1_9.py
  - Fails if any non-archive file contains:
    - schema_version not equal to "1.7" in YAML front matter of examples/template.
    - Spec v other than v1.9 in SSOT set (spec header, linter banner).
    - Linter filename references not equal to ai_task_list_linter_v1_9.py in SSOT docs.
    - LINTER_VERSION major.minor not matching the linter filename major.minor.
  - Fails if `...` occurs in SSOT docs outside fenced code blocks.
  - Fails if `...` occurs inside fenced code blocks but does not match the allowed regex in Ellipsis policy.
  - Reference algorithm (no guessing):
    - parse COMMON.md “Target tuple” values
    - scan markdown files for YAML front matter; if present, enforce schema_version
    - scan allowed-files list for version literals; scan all other files for forbidden literals
    - apply ellipsis checks with fence awareness and allowed regex

## Definition of Done
- `rg 'schema_version: \"1\\.6\"|schema_version: 1\\.6|Spec v1\\.7|ai_task_list_linter_v1_8|README_ai_task_list_linter_v1_8|Spec 1\\.7|schema 1\\.6' . --glob '!*archive*' --glob '!work_folder/*'` returns nothing.
- Guardrail passes (tools/check_version_consistency.py exits 0).
- COMMON.md contains the canonical tuple; other docs either reference COMMON or stay silent on concrete numbers (no conflicting strings).
- Linter banner matches LINTER_VERSION; linter filename matches LINTER_VERSION major.minor.
- Validation suite headers/commands refer to ai_task_list_linter_v1_9.py.
- No non-pattern `...` truncations remain in SSOT docs (spec/COMMON/manuals/template).

## Legacy / migration policy
- task_list_archive/** and **/archive/**: historical; excluded from guardrail/DoD.
- work_folder/**: non-authoritative scratch; excluded from guardrail/DoD.
- canonical_examples/** and templates: MUST be migrated to schema_version "1.7".

## Rollback
- If guardrail or DoD fails after edits: revert the normalization commit(s) as a unit; record offending files/regex matches in VERSION_DRIFT.md; fix and re-run.
