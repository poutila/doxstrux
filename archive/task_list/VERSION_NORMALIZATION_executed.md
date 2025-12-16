# VERSION_NORMALIZATION.md — Plan to Normalize Version Metadata

## Precondition (COMPLETE)
Historical content has been removed from SSOT docs:
- AI_TASK_LIST_SPEC_v1.md: version change annotations removed from rule headings (no "— NEW/UPDATED/FIXED in vX.Y"), version change callout blocks deleted.
- README_ai_task_list_linter_v1_9.md: changelog-style sections removed ("What's Fixed", "Key Changes", "Migration"), rewritten as current-state "Enforcement Features" and "Usage Examples".

Confirmation (must return nothing):
```bash
rg '— (STRENGTHENED|NEW|UPDATED|FIXED) in v\d+' AI_TASK_LIST_SPEC_v1.md README_ai_task_list_linter_v1_9.md
rg '\*\*v\d+\.\d+ (changes?|key change)\*\*:' AI_TASK_LIST_SPEC_v1.md
rg '^## (What.s Fixed|Key Changes|Migration)' README_ai_task_list_linter_v1_9.md
```

---

Goal: One consistent version story across all framework artifacts.
SSOT policy (SSOT set for versions):
- COMMON.md carries the canonical human-readable version tuple.
- AI_TASK_LIST_SPEC_v1.md header is an authoritative contract surface.
- ai_task_list_linter_v1_9.py (LINTER_VERSION + required schema_version enforcement) is an authoritative enforcement surface.
These three MUST match. All other docs MUST either reference COMMON.md (§Version Metadata) or stay silent on concrete numbers.

SSOT docs (normative prose scope for ellipsis/placeholder checks):
- COMMON.md, AI_TASK_LIST_SPEC_v1.md, AI_TASK_LIST_TEMPLATE_v6.md, MANUAL.md (after creation).

COMMON.md parsing (no guessing):
- Find section with heading exactly `## §Version Metadata`.
- If heading not found: guardrail/script MUST fail (no fallback parsing).
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
- COMMON.md: Version metadata (the SSOT tuple), SSOT hierarchy, mode definitions.
- Linter: ai_task_list_linter_v1_9.py banner text; ensure version string matches LINTER_VERSION; rule IDs consistent with spec.
- README_ai_task_list_linter_v1_9.md: Replace concrete version strings with “See COMMON.md §Version Metadata” (keep file name references).
- Manuals: MANUAL.md (after creation), PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md — replace concrete version strings with "See COMMON.md §Version Metadata".
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
  - Current version in non-SSOT files (should be absent): `rg '\\bv1\\.7\\b|schema.*1\\.7' . --glob '!COMMON.md' --glob '!AI_TASK_LIST_SPEC_v1.md' --glob '!ai_task_list_linter_v1_9.py' --glob '!*archive*' --glob '!task_list_archive/**' --glob '!work_folder/**'`

Conflicting strings policy (no guessing):
- No historical or current version literals are allowed outside the SSOT set/allowed files. Any version literal in a non-SSOT file is a violation (no historical exceptions).

## Edits to perform (content-level)
1) Spec:
   - Header: Spec v1.9; schema_version "1.7".
   - Rule IDs: NO renames in this plan. Spec and linter must reference the same IDs. If rule ID renames are desired, do them in a separate plan (e.g., RULE_ID_STABILIZATION.md) as an explicit breaking contract migration.
   - Ellipsis policy (deterministic):
     - Normative prose = any line outside fenced code blocks in SSOT docs (COMMON.md, AI_TASK_LIST_SPEC_v1.md, AI_TASK_LIST_TEMPLATE_v6.md, MANUAL.md).
     - Forbidden: `...` anywhere in normative prose.
     - Allowed inside fenced code blocks only (language {bash, sh}), and only on lines matching: `^(\\$\\s*)?(uv run|rg)\\b.*\\.\\.\\.` (example/command placeholders). Intentional: only `uv run`/`rg` placeholders are allowed; all other commands/comments with `...` are violations. Unlabeled fences (no language) are treated as prose for `...` checks (i.e., `...` forbidden).
2) COMMON:
   - Version block: Spec v1.9, schema 1.7, linter v1_9, template v6.0 (the SSOT tuple).
   - Mode table: template/plan/instantiated, placeholders spelled out.
3) Linter:
   - Banner text: Spec v1.9; schema_version 1.7; three modes.
   - LINTER_VERSION = 1.9.0; ensure docstring reflects it.
   - Filename/version consistency: ai_task_list_linter_v<MAJOR>_<MINOR>.py MUST match LINTER_VERSION major.minor (e.g., 1.9.x → v1_9).
4) README_ai_task_list_linter_v1_9.md:
   - Replace concrete version strings with “See COMMON.md §Version Metadata”; keep file name references. “File name references” = literal filenames/links (e.g., `ai_task_list_linter_v1_9.py`). Update any older filenames (e.g., v1_8) to current.
5) Manuals (MANUAL.md after creation, PROMPT_ORCHESTRATOR):
   - Replace concrete version strings with "See COMMON.md §Version Metadata"; keep schema_version examples at "1.7".
6) Template:
   - Keep schema_version: "1.7" in front matter; elsewhere, reference COMMON for versions.
7) VALIDATION_SUITE.md:
   - Refer to COMMON for version tuple; commands point to ai_task_list_linter_v1_9.py.
8) INDEX.md:
   - Refer to COMMON for version tuple; keep paths accurate.
9) CHANGELOG:
   - Ensure v1.9 entry matches tuple.

## Guardrail (prevent re-drift)
- Add/maintain the consistency check script `tools/check_version_consistency.py` (present in repo) that:
  - Reads the tuple from COMMON.md (per parsing rules above).
  - Excludes: `**/archive/**`, `task_list_archive/**`, `work_folder/**`, `.git/**`.
- Allowed files to contain concrete version literals outside YAML:
   - COMMON.md
   - AI_TASK_LIST_SPEC_v1.md
   - ai_task_list_linter_v1_9.py
   - AI_TASK_LIST_TEMPLATE_v6.md
   - VERSION_NORMALIZATION.md
  - Only the SSOT set above may contain version literals; all other non-excluded files must reference COMMON instead. No historical/version literals allowed elsewhere. canonical_examples/** and validation/** are excluded from version-literal scans.
  - YAML front matter rule: only `schema_version: "1.7"` is allowed; any other version-related fields in YAML are violations.
  - Maintenance: when bumping linter version/filename, update this plan, allowed filename regex/allowlist, and the guardrail script to the new major.minor filename/version.
  - Fails if any non-archive file contains:
    - schema_version not equal to "1.7" in YAML front matter of any markdown file outside exclusion paths (archives/work_folder/task_list_archive/.git).
    - Spec v other than v1.9 in SSOT set (spec header, linter banner).
    - Linter filename references not equal to ai_task_list_linter_v1_9.py in SSOT docs (version-agnostic patterns like `ai_task_list_linter_v*.py` are allowed in code-block shell examples only; prose should use the exact current filename or reference COMMON).
    - LINTER_VERSION major.minor not matching the linter filename major.minor.
    - Any version literals in non-SSOT files (no historical exceptions).
  - Fails if `...` occurs in SSOT docs outside fenced code blocks.
  - Fails if `...` occurs inside fenced code blocks but does not match the allowed regex in Ellipsis policy.
  - Reference algorithm (implemented in the script):
    - parse COMMON.md “Target tuple” values
    - scan markdown files for YAML front matter; if present, enforce schema_version
    - scan allowed-files list for version literals; scan all other files for forbidden literals (no historical exceptions)
    - apply ellipsis checks with fence awareness and allowed regex
    - report first failure with file:path:line and exit non-zero (fail-fast, no auto-fix)

## Definition of Done
- `rg 'schema_version: \"1\\.6\"|schema_version: 1\\.6|Spec v1\\.7|ai_task_list_linter_v1_8|README_ai_task_list_linter_v1_8|Spec 1\\.7|schema 1\\.6' . --glob '!*archive*' --glob '!task_list_archive/**' --glob '!work_folder/*' --glob '!**/archive/**' --glob '!validation/**' --glob '!canonical_examples/**'` returns nothing.
- Historical content absent (precondition confirmation commands return nothing).
- Guardrail passes: `uv run python tools/check_version_consistency.py` exits 0 (fail-fast on first violation).
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

## Post-Execution
After successful execution (all DoD criteria pass):
- Move VERSION_NORMALIZATION.md to `task_list_archive/` as historical planning documentation.
- This file becomes part of the historical record, not active framework documentation.
