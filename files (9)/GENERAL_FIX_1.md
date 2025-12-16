# GENERAL_FIX_1.md — Framework Fix Plan (not file-specific)

## Purpose
Validate and align the already-implemented linter (see COMMON.md for versions/schema; three modes) with spec/COMMON/docs/examples; capture baselines/canaries; and ensure new rules (NEW-01/02/03) are reflected across artifacts. No new linter behavior changes are intended beyond the current v1_9 code.

## Current State Audit (pre-flight; not blocking fixture creation)
**Status:** 🟡 DRAFT — baseline evidence not yet captured; set ownership before execution  
**Owner/Deadline:** Unassigned (must be set before work starts; plan blocked until assigned)

- **A1. Spec ↔ Linter drift (R-ATL-022/075)**  
  Purpose: confirm current linter (v1_9) accepts plan-mode evidence placeholders (no code change intended for R-ATL-022).  
  Command (pre-fix baseline with current linter v1_9):  
  `uv run python ai_task_list_linter_v1_9.py canonical_examples/positives/plan_with_evidence_ph.md`  
  Baseline expected: exit 0 (plan allows placeholders); actual baseline not yet captured (do before coding).  
  Post-fix expected: unchanged (still exit 0 for plan with placeholders). No R-ATL-022 behavior change planned.

- **A2. Coverage phantom references**  
  Status: pending fixture creation in Step 1.  
  Interim: demonstrate gap with an existing file (e.g., a plan referencing missing tasks) and capture linter output once fixture exists.  
  Post-Step-1: `uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/coverage_phantom_refs.md` → Expect R-ATL-NEW-02.

- **A3. Pre-fix validation baseline**  
  Command (pre-fix, current linter v1_9): run all commands in `VALIDATION_SUITE.md`; save summary as `validation/baseline_failures_YYYY-MM-DD.txt` (X/Y positives pass; A/B negatives pass).  
  Actual: baseline not yet captured (do before coding)

## Rule Definitions (for this change)
| Rule | Current Enforcement | Proposed Change | Scope / Grammar |
|------|---------------------|-----------------|-----------------|
| R-ATL-001 | Enforces YAML frontmatter (mode required/valid) | No change; fail fast on missing/invalid mode | Mode must be `template`, `plan`, or `instantiated` (case-sensitive) |
| R-ATL-022 | Rejects `[[PH:*]]` in evidence blocks (plan + instantiated) | Allow in plan; reject in instantiated | Evidence blocks = task-level Evidence, STOP evidence, Global Clean Table evidence |
| R-ATL-075 | Enforces `$` prefix in plan/instantiated | No change | Scope = current linter implementation in `ai_task_list_linter_v1_9.py` (quote behavior verbatim if documenting) |
| R-ATL-NEW-01 | (new) Not enforced | Enforce unique task IDs (no duplicates) | Task headers matching regex `^###\s+Task\s+(\d+\.\d+)` (MULTILINE); capital “Task”; exactly two numeric components; three hashes only (3-level IDs not allowed; use numbered Steps inside a 2-level task instead) |
| R-ATL-NEW-02 | (new) Not enforced | Coverage references must resolve to existing, unique tasks with no gaps | Coverage grammar: single (`1.1`), list (`3.1, 3.4`), range (`2.3-2.5`). Each referenced task ID must exist exactly once; ranges must not skip missing IDs and must not go backward or cross prefixes. |
| R-ATL-NEW-03 | (new) Not enforced | Global Clean Table section required in plan/instantiated modes | Heading must exist: `## Global Clean Table`; missing → error. |

## Goals
1) Plan mode viability: plan can use evidence placeholders; instantiated stays strict; $-prefix enforced in plan/instantiated.
2) Spec/COMMON/Docs/Template/README/Manuals fully aligned with linter (no spec↔tool drift).
3) Internal consistency enforced: unique task IDs; Prose Coverage Mapping references resolve to real, unique tasks (no gaps, no duplicates).
4) Validation strengthened: positives + negatives catch regressions (including coverage-missing-task).
5) (Stretch) Requirement anchors: prepare to map MUST/REQUIRED items from source prose to stable IDs.

## Version semantics
- Spec version: bump to v1.9 (three-mode lifecycle: template/plan/instantiated).
- schema_version: 1.7 (three modes supported; applies to all documents under this framework).
- Linter versioning: create `ai_task_list_linter_v1_9.py` with `LINTER_VERSION = "1.9.0"` (or later) constant exported via `--version`; update all references to use v1_9. Legacy v1_8 is kept in `task_list_archive/` for baselines.

## Evidence block definition (R-ATL-022 scope)
- Evidence headers (regex on line.strip()):
  - Task-level: header matching `^\*\*Evidence\*\*(.*)$` (case-sensitive on “Evidence”; allows suffix after the bold, e.g., `**Evidence** (paste output):`).
  - STOP evidence: header line containing `**Evidence` and `paste` (case-insensitive on paste).
- Evidence blocks: the first fenced code block with language `bash` after the matched evidence header and before the next heading of equal or higher level; skip non-bash fences. Accepted fence language: `bash` only.
  - Task-level Evidence: first bash block after the evidence header.
  - STOP evidence: first bash block after the STOP evidence header.
  - Global Clean Table evidence: section identified by heading exactly `## Global Clean Table` (case-sensitive); collect all bash blocks in that section until the next `##` or `#` heading (prose between is allowed). If heading missing in plan/instantiated, emit missing-section error (R-ATL-NEW-03). Applies to all plan/instantiated documents under this framework (legacy/template artifacts may fail under the new rules).
- Heading detection for “next heading”: lines matching `^#{1,6}\s+` outside fenced code blocks; ignore heading-like text inside fences.
- Mode behavior:
  - template: placeholders allowed (commands and evidence).
  - plan: placeholders allowed in evidence blocks.
  - instantiated: placeholders forbidden; real output required. Each evidence bash block must contain at least one `$` command line and at least one non-placeholder line. Commands that produce no output are allowed if the block contains an explicit marker such as `# no output (command silent)`.

## Artifact inventory (paths in this repo)
- Linter: `ai_task_list_linter_v1_9.py` (new; add `LINTER_VERSION` constant)
- Spec/COMMON: `AI_TASK_LIST_SPEC_v1.md`, `COMMON.md`
- Docs: `INDEX.md`, `README_ai_task_list_linter_v1_9.md`, `USER_MANUAL.md`, `AI_ASSISTANT USER_MANUAL.md`
- Template/examples: `AI_TASK_LIST_TEMPLATE_v6.md`, `canonical_examples/positives/`, `canonical_examples/negatives/` (add: instantiated_with_placeholders.md, duplicate_task_ids.md, coverage_phantom_refs.md)
- Validation outputs: `VALIDATION_SUITE.md` (commands), `validation/baseline_failures_*.txt` (generated)

## Mode detection (R-ATL-022 dependency)
- Source: YAML frontmatter `ai_task_list.mode` (required; case-sensitive).
- Valid: `template`, `plan`, or `instantiated` (case-sensitive).
- Errors: missing frontmatter/mode/invalid → R-ATL-001 (fail fast).

## Scope
- Linter: plan-mode evidence allowance; plan/instantiated $-prefix (aligned to current linter heuristic, not narrowed to arrays only); internal consistency checks (unique task IDs; coverage references resolve + unique). No new runtime dependencies; keep linter stdlib-only plus existing uv/rg usage in fixtures.
- Spec/COMMON: mirror linter (plan allows evidence placeholders; coverage must reference existing tasks and uniqueness).
- Docs/Template/README/Manuals/INDEX: reflect rules; ensure COMMON.md is discoverable; update references to reflect the three-mode lifecycle (template/plan/instantiated), schema_version 1.7. Legacy artifacts in `work_folder/` that still reference v1_8/schema 1.6 are out of scope for this plan; either migrate them to schema 1.7 before linting or ignore them for this change set.
- Validation: keep examples/negatives aligned with enforcement (add missing coverage-negative and enforce suite format); keep test fixture names consistent with repo (use existing `example_plan.md` / `example_instantiated.md` or explicitly create the new ones listed below).
- Canary safety net: pre/post canary run with manifest to enable rollback.
- External dependencies: no new linter deps (stdlib-only). Required tools for fixtures/DoD: Python ≥3.10, uv ≥0.1.0, ripgrep ≥13.0, bash ≥4.0. Execution convention: run all python scripts via `uv run python ...`; do not invoke system `python` or `pip` directly.
- Lifecycle: support three modes — `template`, `plan`, and `instantiated`. template: placeholders allowed. plan: real commands, evidence placeholders allowed. instantiated: real evidence, placeholders forbidden. schema_version is 1.7.

## Change Impact / Order
1) Spec (SSOT for contract)
2) Linter (implements spec changes)
3) COMMON (imports spec/linter behavior)
4) Docs/Template/README/Manuals/INDEX (sync to COMMON/spec)
5) Validation fixtures/suite (positives/negatives)

## Steps
### 1) Linter
- R-ATL-022: allow evidence placeholders in plan (all evidence blocks); instantiated forbids placeholders and requires real output.
- R-ATL-075: NO CODE CHANGES. Scope = current linter implementation in `ai_task_list_linter_v1_9.py`; do not reinterpret. Current behavior (quote verbatim if needed): scan fenced code blocks in Task Preconditions (non–Phase 0), TDD Step 3 — Verify (GREEN), Phase Unlock Artifact, and Global Clean Table Scan. In those blocks, any command-like line (e.g., contains `rg`, `pytest`, `uv run`, `python`, etc.) must start with `$`; otherwise emit R-ATL-075. Do not change this logic.
- Internal consistency: enforce unique task IDs; coverage references must resolve to existing, unique tasks (single/list/range, no gaps; each referenced task header appears exactly once). Parsing rules: split on comma, trim empties; range must be two parts, same prefix, forward only, dotted numbers only; expand ranges to validate gaps; error on malformed/backward/cross-prefix.
  - Task ID regex (R-ATL-NEW-01): `^###\s+Task\s+(\d+\.\d+)` (MULTILINE); match only three hashes, capital “Task”, two numeric components; do NOT match lower-case, no-space, extra hashes, or three-level IDs. Apply only outside fenced code blocks (same fence-stripping logic as heading detection) to avoid false matches inside fences.
- Coverage parsing (R-ATL-NEW-02): split on commas; item is single or range (exactly one dash). Range validation: both ends match `\d+\.\d+`, same prefix, start <= end, no cross-prefix; expand ranges to detect gaps/backwards; errors on malformed/backward/cross-prefix/invalid formats.
- R-ATL-NEW-01 algorithm (code to add): iterate all matches of the task regex; track first occurrence line; on repeat emit `R-ATL-NEW-01: Duplicate task ID '<id>' at lines <first> and <current>`. Use dict task_id → first line; line numbers via newline count before match.start().
- R-ATL-NEW-02 algorithms (code to add):
  - `parse_coverage_entry(entry)`: items = comma-split trimmed non-empty; for item with dash → `expand_range`; else require `^\d+\.\d+$` or raise ValueError.
  - `expand_range(range_str)`: exactly one dash; both ends match `^(\d+)\.(\d+)$`; prefixes equal; start <= end; return expanded list `[f"{prefix}.{i}" for i in range(start,end+1)]`; raise ValueError on malformed/backward/cross-prefix/invalid ends.
  - Validation: for each referenced ID from parse, count occurrences in doc task IDs; count==0 → “Coverage references task '<id>' which does not exist”; count>1 → “Task '<id>' appears <count> times (ambiguous)”. Parse errors reported as `Coverage parse error: <msg>`.
- Coverage extraction (R-ATL-NEW-02): extract only from the first markdown table after heading `## Prose Coverage Mapping`.
  - Accepted headers (case-sensitive): {Implemented by Task(s), Implemented by Tasks, Tasks, Task IDs}.
  - If multiple accepted headers exist: use canonical if present, else leftmost accepted. If none: R-ATL-NEW-02 “missing Implemented-by column”.
  - Table definition: contiguous block where line 1 starts with `|` and has ≥3 `|`; line 2 is a separator row starting with `|` and containing `---` per column (alignment with optional colons `:---`, `---:`, `:---:` allowed); subsequent lines start with `|`; stop at blank line or next heading.
- Add/update fixtures to match repo naming: required positives = `canonical_examples/positives/example_template.md`, `canonical_examples/positives/example_plan.md`, `canonical_examples/positives/example_instantiated.md` (no alternates); required negatives = `canonical_examples/negatives/plan_preconditions_placeholder.md`, `canonical_examples/negatives/plan_missing_coverage_mapping.md`, `canonical_examples/negatives/template_missing_clean_table_placeholder.md` — each with explicit violation placement.
- Validation suite schema: document required structure in `VALIDATION_SUITE.md` (categories: plan positives, instantiated positives, negatives; each test has File/Command/Expected/Status/Last run; summary totals). The task-list linter does not enforce this; execution is via the listed commands.
- Clarify mode detection: fail if mode missing/invalid in frontmatter; valid values = template|plan|instantiated (case-sensitive).

### 2) Spec/COMMON
- Clarify plan vs instantiated evidence rules.
- State coverage references must point to existing, unique tasks (single/list/range allowed; ranges no gaps; references cannot point to non-existent or duplicate task IDs).
- Keep version metadata consistent with COMMON (spec to v1.9; schema_version 1.7).
- Linter versioning already decided: release `ai_task_list_linter_v1_9.py` with `LINTER_VERSION = "1.9.0"` and update references.
- Spec exact edit locations:
  - Line 1: change `# AI Task List Specification v1.7` → `# AI Task List Specification v1.9`.
  - Section 4 “Document Structure”: after current Evidence Blocks subsection, add `#### 4.2.1 Evidence Placeholders (Mode-Dependent)`:
    - Plan: evidence blocks MAY contain `[[PH:UPPERCASE_NAME]]` placeholders (format `[[PH:` + uppercase identifier + `]]`; examples `[[PH:OUTPUT]]`, `[[PH:TEST_RESULTS]]`).
    - Instantiated: evidence blocks MUST contain real output; placeholders forbidden (R-ATL-022).
  - Section 5 “Prose Coverage Mapping”: add `#### 5.3 Coverage Reference Integrity (R-ATL-NEW-02)` stating coverage references must point to existing, unique tasks; allowed forms single/list/range; ranges same prefix, forward, no gaps; references to missing or duplicate task IDs are errors.
    - Extraction: coverage references are taken only from the first markdown table after `## Prose Coverage Mapping`, column header accepted set (case-sensitive): {Implemented by Task(s), Implemented by Tasks, Tasks, Task IDs}. If multiple accepted headers exist, use canonical if present, else leftmost accepted. If none, raise R-ATL-NEW-02 “missing Implemented-by column”. Table definition: contiguous block where line 1 starts with `|` and has ≥3 `|`; line 2 is a separator row starting with `|` and containing `---` per column; subsequent lines start with `|`; stop at blank line or next heading.
  - COMMON exact edits:
  - Evidence Requirements section: add paragraph mirroring plan vs instantiated placeholder rules (plan may use placeholders; instantiated requires real output; placeholders forbidden).
  - Add section `## Coverage Mapping Integrity` stating references must resolve to existing, unique tasks; single/list/range allowed; ranges same prefix, forward, no gaps; errors if missing/duplicate. Extraction: from the first table under `## Prose Coverage Mapping`, column accepted set (case-sensitive): {Implemented by Task(s), Implemented by Tasks, Tasks, Task IDs}. If multiple accepted, prefer canonical else leftmost; if none, error “missing Implemented-by column”. No other sources.

### 3) Docs/Template
- Ensure version/mode/evidence notes match linter/spec; COMMON listed in INDEX.
- Keep examples/negatives in sync with enforcement (plan evidence allowed; instantiated forbids).
- Clarify coverage reference grammar (single, list, ranges) and evidence scope in user-facing docs.

- Phase A (pre-fix): run current `VALIDATION_SUITE.md`, record failures (baseline_failures.txt).
- Phase B (post-fix): rerun full suite (positives + negatives, including coverage-missing-task) and update results in `VALIDATION_SUITE.md`.
- Execution model: use the prescribed commands in `VALIDATION_SUITE.md` (no optional path; manual copy/paste of listed commands). A helper script can be added later, but the canonical run is the commands written in the suite.
- Canary set: select 10 task lists intended to remain valid under new rules (5 plan, 5 instantiated); store under `validation/canaries/` with MANIFEST.md and baseline logs; rerun post-fix; rollback if >2 new failures. Use repo-local task lists if external ones are unavailable; minimum acceptable set = 8 (4/4) with rollback threshold >1.
- Negative fixtures (exact content to add under `canonical_examples/negatives/`):
  - `instantiated_with_placeholders.md` (instantiated):
    ```
    ---
    ai_task_list:
      schema_version: "1.7"
      mode: "instantiated"
      runner: "uv"
    ---

    # Test: Instantiated Mode Rejects Placeholders

    ### Task 1.1 — Test Evidence Placeholder

    **Evidence** (paste actual output):
    ```bash
    $ uv run pytest -q
    [[PH:OUTPUT]]
    ```

    - [ ] Task complete
    ```
  - `duplicate_task_ids.md` (plan):
    ```
    ---
    ai_task_list:
      schema_version: "1.7"
      mode: "plan"
      runner: "uv"
    ---

    # Test: Duplicate Task IDs

    ### Task 1.1 — First Instance

    **Steps:**
    1. Do something

    - [ ] Complete

    ### Task 1.2 — Intermediate Task

    **Steps:**
    1. Do something else

    - [ ] Complete

    ### Task 1.1 — Duplicate Instance

    **Steps:**
    1. This is a duplicate task ID

    - [ ] Complete
    ```
  - `coverage_phantom_refs.md` (plan):
    ```
    ---
    ai_task_list:
      schema_version: "1.7"
      mode: "plan"
      runner: "uv"
    ---

    # Test: Coverage Phantom References

    ## Prose Coverage Mapping

    | Prose Requirement | Source Location | Implemented by Task(s) |
    |-------------------|-----------------|------------------------|
    | Add logging | Spec §3.1 | 1.1 |
    | Create tests | Spec §3.2 | 2.1 |
    | Deploy changes | Spec §3.3 | 3.1 |

    ---

    ### Task 1.1 — Add Logging

    **Steps:**
    1. Add logging statements

    - [ ] Complete

    ### Task 3.1 — Deploy Changes

    **Steps:**
    1. Deploy to production

    - [ ] Complete
    ```
- `VALIDATION_SUITE.md` format (must follow; create if absent):
  ```
  # AI Task List Validation Suite

  ## Metadata
  **Last run:** YYYY-MM-DD HH:MM:SS
  **Linter version:** ai_task_list_linter_v1_9.py (LINTER_VERSION=1.9.0)
  **Runner:** uv

  ---

  ## Category: Plan Mode Positives

  ### Test P1: Evidence placeholders allowed
  **File:** `canonical_examples/positives/plan_with_evidence_ph.md`
  **Command:**
  ```bash
  $ uv run python ai_task_list_linter_v1_9.py canonical_examples/positives/plan_with_evidence_ph.md
  ```
  **Expected:** Exit 0 (no errors)
  **Status:** ⬜ NOT RUN
  **Last run:** N/A

  ---

  ## Category: Instantiated Mode Positives

  ### Test I1: Real evidence accepted
  **File:** `canonical_examples/positives/example_instantiated.md`
  **Command:**
  ```bash
  $ uv run python ai_task_list_linter_v1_9.py canonical_examples/positives/example_instantiated.md
  ```
  **Expected:** Exit 0
  **Status:** ⬜ NOT RUN
  **Last run:** N/A

  ---

  ## Category: Negatives

  ### Test N1: Instantiated rejects placeholders
  **File:** `canonical_examples/negatives/instantiated_with_placeholders.md`
  **Command:**
  ```bash
  $ uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/instantiated_with_placeholders.md 2>&1 | rg "R-ATL-022"
  ```
  **Expected:** Match found (R-ATL-022 present)
  **Status:** ⬜ NOT RUN
  **Last run:** N/A

  ### Test N2: Duplicate task IDs
  **File:** `canonical_examples/negatives/duplicate_task_ids.md`
  **Command:**
  ```bash
  $ uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/duplicate_task_ids.md 2>&1 | rg "R-ATL-NEW-01"
  ```
  **Expected:** Match found (R-ATL-NEW-01 present)
  **Status:** ⬜ NOT RUN
  **Last run:** N/A

  ### Test N3: Coverage phantom references
  **File:** `canonical_examples/negatives/coverage_phantom_refs.md`
  **Command:**
  ```bash
  $ uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/coverage_phantom_refs.md 2>&1 | rg "R-ATL-NEW-02"
  ```
  **Expected:** Match found (R-ATL-NEW-02 present)
  **Status:** ⬜ NOT RUN
  **Last run:** N/A

  ---

  ## Summary

  **Plan Mode Positives:** X/Y passed
  **Instantiated Mode Positives:** A/B passed
  **Negatives:** C/D failed correctly

  **Overall Status:** ⬜ NOT RUN

  **Thresholds:**
  - Positives: 100% must pass (exit 0)
  - Negatives: 100% must fail correctly (expected error present)
  ```
- Canary process (closed set): use all `.md` files under `canonical_examples/positives/` that declare `schema_version: "1.7"` and `mode: template|plan|instantiated`. Copy to `validation/canaries/`; run baseline `uv run python ai_task_list_linter_v1_9.py <file>` for each to `baseline.txt` (expect 0 fails); create `validation/canaries/MANIFEST.md` with file/mode/source/status; post-fix rerun to `post_fix.txt`; rollback if >2 new failures (or >1 if only 8 canaries). Do not add files from other folders; do not include known-invalid examples.

## Definition of Done (testable)
- Automated (all must pass):
  - Plan evidence allowed: `uv run python ai_task_list_linter_v1_9.py canonical_examples/positives/plan_with_evidence_ph.md`
  - Instantiated evidence rejected: `uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/instantiated_with_placeholders.md | rg R-ATL-022`
  - Unique task IDs: `uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/duplicate_task_ids.md | rg R-ATL-NEW-01`
  - Coverage references resolve: `uv run python ai_task_list_linter_v1_9.py canonical_examples/negatives/coverage_phantom_refs.md | rg R-ATL-NEW-02`
  - Spec/common wording sync: `rg "plan.*placeholder" AI_TASK_LIST_SPEC_v1.md COMMON.md`
  - COMMON listed: `rg "COMMON\\.md" INDEX.md`
  - Full suite: run all commands in `VALIDATION_SUITE.md` (positives must all pass; negatives must all fail with expected errors).
- Manual:
  - Current State Audit completed (A1–A3 filled).
- Spec version bumped to v1.9 (rules changed: R-ATL-NEW-01/02/03 added; R-ATL-022 modified); schema_version set to 1.7 (template/plan/instantiated).
  - Rule definitions present in spec/COMMON for changed/added rules.
  - Peer review of spec/COMMON/doc wording (plan vs instantiated evidence).
  - VALIDATION_SUITE.md follows required schema (categories + File/Command/Expected/Status/Last run; summary present).
  - Canary manifest present; baseline and post-fix logs stored; rollback criterion evaluated.
- No placeholders remain in this plan: `[NAME]`, `[DATE]`, `[PASTE` all resolved. Allowed literals: date/time stamps (YYYY-MM-DD, HH:MM:SS), simple counters (X/Y), and “NOT RUN” markers. Verify via `rg '\[NAME\]|\[DATE\]|\[PASTE' GENERAL_FIX_1.md` → expect no matches.

## Rollback & Regression Prevention
- Rollback: if >2 previously valid canaries fail post-change, revert linter/spec changes and note known issue in COMMON.
- Regression prevention: add CI checks to lint spec examples and check rule ID consistency; require spec+linter co-change review checklist; add spec-example validation and rule-ID sync tests.

## External Dependencies (Ubuntu-only)
- Python ≥3.10, uv, ripgrep ≥13.0, bash ≥4.0 — already installed; no install steps in this plan.
- Execution convention: run all python scripts via `uv run python ...`; do not invoke system `python` or `pip` directly.

## Timeline
- Approx 2 days (Phase 0 + Step 1 on Day 1; Steps 2–4 on Day 2).
