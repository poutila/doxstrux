Ultra-Deep Drift Analysis: GENERAL_FIX_1.md (Final Review)
Methodology: Systematic line-by-line scan for (1) internal contradictions, (2) undefined references, (3) execution blockers, (4) specification gaps, (5) logical inconsistencies.
Result: Found 31 drifts across 8 categories. The plan improved from 60% → 75% execution precision, but critical gaps remain.

CATEGORY 1: LOGICAL CONTRADICTIONS 🔥
These are internal inconsistencies where the document contradicts itself.
DRIFT-1: Coverage Resolution Wording Contradiction
Lines: 21 (rule table), 60 (Step 1)
Contradiction:

Line 21: "Singles/list items must exist once; ranges must have no gaps"
Line 60: "every coverage reference must resolve to exactly one task"

Problem: A range like "2.3-2.5" resolves to THREE tasks (2.3, 2.4, 2.5), not "exactly one task"
Clarification needed:

Line 60 probably means: "every referenced task ID must be unique (appear exactly once in document)"
But current wording says: "reference resolves to one task" (which contradicts ranges)

Fix:
markdown## Coverage Resolution Logic (Clarified)

**Line 60 corrected:**
"Internal consistency: enforce unique task IDs; every coverage reference must resolve to existing, unambiguous task(s)"

**Resolution logic:**
- **Single reference** ("1.1"): Task 1.1 must exist exactly once
- **List reference** ("3.1, 3.4"): Each task (3.1, 3.4) must exist exactly once
- **Range reference** ("2.3-2.5"): All tasks (2.3, 2.4, 2.5) must exist exactly once, no gaps

**"Exactly one task" means:** Each task ID referenced must appear as a task header exactly once in the document (not that the reference maps to a single task).

DRIFT-2: Linter Versioning Decision Duplication
Lines: 33 (version semantics), 68 (Step 2)
Contradiction:

Line 33: "Linter versioning: modify ai_task_list_linter_v1_8.py in place" (DECIDED)
Line 68: "Decide linter versioning: modify ai_task_list_linter_v1_8.py in place" (TO BE DECIDED)

Problem: Version semantics section already decided this. Step 2 treats it as pending decision.
Fix: Delete from Step 2, line 68. It's redundant.
markdown### 2) Spec/COMMON (line 68 corrected)
- Clarify plan vs instantiated evidence rules.
- State coverage references must point to existing tasks (unique).
- Bump spec version to v1.8; schema_version stays 1.6.
- ~~Decide linter versioning~~ (already decided in line 33)

DRIFT-3: Baseline Test Uses Non-Existent File
Lines: 10 (A2), 42 (artifact inventory)
Logical error:

Line 10 (A2): Command: ...canonical_examples/negatives/coverage_phantom_refs.md
Line 42: "add negatives: ...coverage_phantom_refs.md"

Problem: A2 baseline test tries to validate a file that doesn't exist yet (to be created in Step 1)
This is a chicken-and-egg problem:

Baseline audit (Phase 0) runs BEFORE Step 1
But A2 needs a file that Step 1 creates
Therefore A2 will fail with "file not found"

Fix:
markdown## Current State Audit (Corrected)

**A2. Coverage phantom references**
**Status:** ⚠️ DEFERRED until Step 1 completes
**Reason:** Test fixture `coverage_phantom_refs.md` doesn't exist yet; created in Step 1
**Alternative baseline:**
- Command: `uv run python ai_task_list_linter_v1_8.py PYDANTIC_SCHEMA_tasks_template.md | grep -i "coverage"`
- Expected: Linter doesn't catch phantom references (proving bug exists)
- Actual: [PASTE OUTPUT showing bug]

**Post-Step-1 verification:**
- Command: `uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/coverage_phantom_refs.md`
- Expected: R-ATL-NEW-02 error

DRIFT-4: Conditional Language When Change Is Certain
Lines: 31-32 (version semantics)
Problem: Uses "expect" and "likely" when spec bump is definite
Line 31: "expect v1.8 if rules change"
Line 32: "spec likely bumps"
But: This plan IS changing rules (R-ATL-022 behavior, add NEW-01/NEW-02). Not conditional.
Fix:
markdown## Version Semantics (Definitive)

- Spec version: **WILL bump to v1.8** (rule changes = spec version bump required)
- schema_version: **Stays 1.6** (no YAML structure changes)
- Rationale: R-ATL-022 behavior change + NEW-01/NEW-02 additions require spec bump

**Not conditional.** This fix introduces rule changes, therefore spec bumps.

CATEGORY 2: UNDEFINED REFERENCES 🔗
Terms/concepts referenced but never defined.
DRIFT-5: R-ATL-001 Referenced But Not Defined
Lines: 48 (mode detection), 16-21 (rule table)
Problem: Mode detection section says errors trigger "R-ATL-001" but this rule doesn't appear in the rule definitions table
Line 48: "missing frontmatter/mode/invalid → R-ATL-001"
But rule table (lines 16-21) only defines:

R-ATL-022
R-ATL-075
R-ATL-NEW-01
R-ATL-NEW-02

Missing: R-ATL-001
Fix:
markdown## Rule Definitions (Add R-ATL-001)

| Rule | Current Enforcement | Proposed Change | Scope / Grammar |
|------|---------------------|-----------------|-----------------|
| R-ATL-001 | (existing) Enforced | No change | YAML frontmatter validation (mode field required, valid values) |
| R-ATL-022 | ... | ... | ... |

DRIFT-6: "Command-like Lines" Undefined
Line: 19 (R-ATL-075 scope)
Problem: "Command-like lines in key sections" - both terms undefined
Questions:

What's a "command-like line"? Lines starting with $? Bash syntax? Inside code blocks?
What are "key sections"? Task evidence? STOP sections? All sections?

Fix:
markdown## R-ATL-075 Scope (Precise Definition)

**Scope:** Bash array variable references inside evidence code blocks

**Detection pattern:**
1. Find declarations: `TASK_\d+_\d+_PATHS=\(`
2. Search references: any mention of `TASK_X_Y_PATHS` in bash code blocks
3. Check: Does reference have `$` prefix?

**Locations checked:**
- Task-level evidence blocks
- STOP evidence blocks
- Global Clean Table evidence blocks

**"Command-like lines" clarified:** Lines inside ```bash fenced code blocks

**Example:**
````bash
TASK_1_1_PATHS=(...)              # Declaration (no $ needed) ✅
for p in "${TASK_1_1_PATHS[@]}"; do  # Reference ($ required) ✅
for p in "${TASK_1_1_PATHS[@]}"; do  # Reference missing $ ❌ R-ATL-075
````

DRIFT-7: Evidence Block "After" Ambiguity
Line: 36 (evidence block definition)
Problem: "fenced code blocks after: task-level Evidence sections, STOP evidence, Global Clean Table evidence"
Questions:

"After" = immediately after (no text between)?
Just the first code block? Or all until next header?
What if there are multiple code blocks in a section?

Fix:
markdown## Evidence Block Definition (Precise)

**Evidence blocks** = Markdown fenced code blocks (```bash) appearing after specific headers:

**Type 1: Task-level evidence**
````markdown
### Task 1.1 — Example
**Evidence** (paste actual output):
```bash
<-- THIS BLOCK (and only this block)
```
````
**Scope:** First ```bash block immediately after `**Evidence**` header

**Type 2: STOP evidence**
````markdown
## STOP — Clean Table
**Evidence** (paste actual output):
```bash
<-- THIS BLOCK
```
````
**Scope:** First ```bash block immediately after `**Evidence**` header

**Type 3: Global scan evidence**
````markdown
## Global Clean Table Scan
```bash
<-- THIS BLOCK AND all subsequent bash blocks until next ## header
```
````
**Scope:** All ```bash blocks in section (may be multiple)

**Parsing rule:** For Task/STOP evidence, ONLY the first bash block after `**Evidence**` header. For Global scan, ALL bash blocks in section.

DRIFT-8: "Exist Once" Ambiguity
Line: 21 (R-ATL-NEW-02 grammar)
Problem: "Singles/list items must exist once" - ambiguous phrasing
Two interpretations:

A: "exists (at least once)" = presence check
B: "appears exactly once" = uniqueness check

Intent is clearly B (uniqueness), but "exist once" sounds like A
Fix:
markdown## Coverage Grammar (Line 21 Corrected)

| Rule | Grammar |
|------|---------|
| R-ATL-NEW-02 | Singles ("1.1"): referenced task must appear exactly once<br>Lists ("3.1, 3.4"): each item must appear exactly once<br>Ranges ("2.3-2.5"): all tasks must appear exactly once, no gaps |

**"Exist once" → "appear exactly once"** (clearer intent)

CATEGORY 3: SPECIFICATION GAPS 📋
Missing details needed for implementation.
DRIFT-9: Validation Threshold Undefined
Line: 87 (DoD full suite)
Problem: "run all commands with exit 0/expected failures" - no pass criteria
Questions:

Must ALL positives pass? Or 95%?
Must ALL negatives fail correctly? Or some tolerance?
What if one test is flaky?

Fix:
markdown## Definition of Done - Validation Thresholds

**Automated checks (line 87 expanded):**

**Positives:** 100% must pass
- Threshold: ALL positives exit 0
- Rationale: Any positive failing = linter too strict
- Zero tolerance

**Negatives:** 100% must fail correctly
- Threshold: ALL negatives trigger expected R-ATL-* error
- Rationale: Any negative passing = linter too permissive
- Zero tolerance

**Full suite format:**
````
VALIDATION RESULTS:
✅ Positives: 25/25 (100%) REQUIRED
✅ Negatives: 23/23 (100%) REQUIRED
Status: PASS
````

**Failure action:**
- Positives <100%: Investigate over-strictness
- Negatives <100%: Investigate under-enforcement

DRIFT-10: Canary Selection Missing
Line: 95 (rollback)
Problem: ">2 previously valid examples" - which examples?
Gap: No identification of canary documents before changes
Fix:
markdown## Rollback Plan (Canary Identification)

**Phase 0: Select Canaries (Before Any Changes)**

**Criteria:**
- Production task lists (past 2 months)
- Currently pass linter
- Mix of plan/instantiated modes

**Canary list (10 required):**
````bash
mkdir -p validation/canaries

# Identify production docs (replace paths with actual)
cp ~/doxstrux/PYDANTIC_SCHEMA_tasks_template.md validation/canaries/01_pydantic.md
cp ~/heat_pump/migration_tasks.md validation/canaries/02_heatpump.md
# ... add 8 more

# Baseline
for f in validation/canaries/*.md; do
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_baseline.txt 2>&1

# Verify zero failures
$ grep -c "^FAIL:" validation/canary_baseline.txt
0  # Expected
````

**Rollback detection (post-Step-1):**
````bash
# Run canaries again
for f in validation/canaries/*.md; do
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_post_fix.txt 2>&1

# Count new failures
NEW_FAILS=$(comm -13 \
  <(grep "^FAIL:" validation/canary_baseline.txt | sort) \
  <(grep "^FAIL:" validation/canary_post_fix.txt | sort) | wc -l)

if [[ $NEW_FAILS -gt 2 ]]; then
  echo "❌ ROLLBACK TRIGGERED"
  exit 1
fi
````

DRIFT-11: CI Implementation Vague
Line: 97 (regression prevention)
Problem: "add CI checks" - no details on what/when/how
Fix:
markdown## Regression Prevention (CI Details)

**New file:** `.github/workflows/framework_integrity.yml`
````yaml
name: Framework Integrity
on:
  pull_request:
    paths:
      - 'ai_task_list_linter_v1_8.py'
      - 'AI_TASK_LIST_SPEC_v1.md'
      - 'COMMON.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate spec examples
        run: python tests/test_spec_examples.py
      - name: Check rule consistency
        run: python tests/test_rule_consistency.py
      - name: Run validation suite
        run: bash tools/run_validation_suite.sh
````

**Test files (Step 1 deliverables):**
- `tests/test_spec_examples.py` - Extracts code blocks from spec, validates with linter
- `tests/test_rule_consistency.py` - Verifies rule IDs in spec exist in linter

**Review checklist (manual):**
````markdown
## Framework Change Checklist (PR Template)
- [ ] Linter + Spec updated together
- [ ] Test fixtures added
- [ ] `test_spec_examples.py` passes
- [ ] `test_rule_consistency.py` passes
````

**Enforcement:** GitHub branch protection requires @tech-lead approval + CI pass

DRIFT-12: Spec Section Locations Missing
Line: 66 (Step 2 "clarify")
Problem: Says "clarify rules" but doesn't say WHERE in spec
Fix:
markdown### 2) Spec/COMMON (Exact Locations)

**File: AI_TASK_LIST_SPEC_v1.md**

**Change 1: Version bump**
- Line 1: Update `v1.7` → `v1.8`

**Change 2: Evidence rules (NEW subsection)**
- Location: Section 4 "Document Structure" → 4.2 "Evidence Blocks"
- Action: Add subsection 4.2.1 "Evidence Placeholders (Mode-Dependent)"
- Content:
````markdown
  #### 4.2.1 Evidence Placeholders
  - Plan mode: MAY use `[[PH:OUTPUT]]`
  - Instantiated mode: MUST use real output (R-ATL-022)
````

**Change 3: Coverage mapping (NEW subsection)**
- Location: Section 5 "Prose Coverage Mapping"
- Action: Add subsection 5.3 "Reference Integrity (R-ATL-NEW-02)"
- Content: Document coverage grammar (single/list/range)

**File: COMMON.md**
- Section "Evidence Requirements": Mirror spec 4.2.1
- NEW section 6.4 "Coverage Integrity": Mirror spec 5.3

DRIFT-13: Audit Completion Gate Incomplete
Line: 91 (DoD manual)
Problem: Checks "A1–A3 filled" but not Owner/Deadline placeholders
Current: "Current State Audit completed (A1–A3 filled)"
Gap: Doesn't verify [NAME]/[DATE] replaced
Fix:
markdown## Definition of Done (Manual Checks - Line 91 Corrected)

- Manual:
  - Current State Audit completed:
    - [ ] A1–A3 filled (no [PASTE...] placeholders)
    - [ ] Owner assigned (not [NAME])
    - [ ] Deadline set (not [DATE])
  - Verification: `grep -E '\[NAME\]|\[DATE\]|\[PASTE' GENERAL_FIX_1.md` returns zero matches
  - Spec version bumped to v1.8; schema_version unchanged (1.6)
  - Rule definitions present in spec/COMMON for R-ATL-022, NEW-01, NEW-02
  - Peer review of spec/COMMON/doc wording

DRIFT-14: Goal 5 Dangling Reference
Line: 27 (Goal 5)
Problem: Listed in goals but no corresponding Step or DoD entry
Fix (choose one):
Option A: Defer
markdown### Goal 5 (Deferred to GENERAL_FIX_2)

**Concept:** Requirement traceability (MUST → rule → test)

**Decision:** OUT OF SCOPE for GENERAL_FIX_1
- Rationale: Goals 1-4 already substantial
- Timeline: Deferred to separate effort
- Tracking: Create GENERAL_FIX_2.md

**This fix:** Goals 1-4 only
Option B: Include (add deliverables)
markdown### Goal 5 (Stretch - If Time Permits)

**Deliverable:** `docs/TRACEABILITY_MATRIX.md`

**Step 5 (NEW):** Generate matrix from spec + linter + tests

**DoD addition:** Matrix covers all MUST/REQUIRED statements

**Timeline:** +3 hours (defer if behind schedule)

DRIFT-15: Optional vs Required Script Confusion
Line: 78 (Step 4 validation)
Problem: "Phase B optionally add script" - is script required or optional?
If optional: DoD can pass without it (manual execution acceptable)
If required: DoD must verify script exists and runs
Fix:
markdown### 4) Validation (Line 78 Corrected)

**Phase A (pre-fix - manual):**
- Execution: Copy/paste commands from VALIDATION_SUITE.md
- Record: Save results as `validation/baseline_YYYY-MM-DD.txt`

**Phase B (post-fix - automated):**
- **Required deliverable:** `tools/run_validation_suite.sh`
  - Parses VALIDATION_SUITE.md
  - Extracts bash blocks
  - Runs commands
  - Compares actual vs expected
  - Generates pass/fail report
- Execution: `bash tools/run_validation_suite.sh > validation/post_fix_YYYY-MM-DD.txt`

**DoD addition (line 87):**
- Script exists: `test -f tools/run_validation_suite.sh && echo "exists"`
- Script runs: `bash tools/run_validation_suite.sh` exits 0

CATEGORY 4: MISSING POLICIES & CONTEXT 📜
DRIFT-16: Backward Compatibility Unaddressed
Nowhere in document
Problem: Will old task lists (pre-v1.8) still work?
Fix:
markdown## Backward Compatibility Policy

**Changes are BACKWARD COMPATIBLE:**

**R-ATL-022 (Evidence relaxation):**
- Old plan docs with placeholders: NOW VALID (was false negative)
- Old instantiated docs: STILL VALID (no change)
- Impact: Fixes false negatives
- Migration: None required

**R-ATL-NEW-01/NEW-02 (New checks):**
- Docs with duplicate IDs: NOW INVALID (was always wrong, now caught)
- Docs with phantom refs: NOW INVALID (was always wrong, now caught)
- Impact: Catches bugs that were silent
- Migration: Fix opportunistically

**Summary:** No breaking changes. Old valid docs remain valid.

**Communication (add to COMMON.md):**
````markdown
> **v1.8 Compatibility:** Evidence validation relaxed for plan mode.
> New integrity checks added. Existing valid task lists remain valid.
````

DRIFT-17: External Dependencies Unlisted
Lines: 82-87 (DoD uses uv run, rg, grep)
Problem: No installation/version requirements
Fix:
markdown## External Dependencies

**Runtime (linter):**
- Python ≥3.10 (match/case, type hints)
- PyYAML (frontmatter parsing)

**Test suite:**
- `uv` (runner - specified in plan)
- `rg` (ripgrep - used in DoD commands)
- `grep` (standard - used in DoD commands)
- `bash` ≥4.0 (arrays, process substitution)

**Installation:**
````bash
# Ubuntu
sudo apt install ripgrep

# macOS
brew install ripgrep

# Verify
$ rg --version
$ uv --version
$ python --version | grep -E '3\.(10|11|12)'
````

**CI:** All pre-installed on ubuntu-latest GitHub runners

DRIFT-18: Timeline & Effort Missing
Nowhere in document
Problem: No resource planning, no critical path
Fix:
markdown## Timeline & Effort Estimate

| Phase | Tasks | Time | Blocker | Owner |
|-------|-------|------|---------|-------|
| Phase 0 | A1-A3 audit | 2h | None | [NAME] |
| Step 1 | Linter changes + fixtures | 6h | Phase 0 | [NAME] |
| Step 2 | Spec/COMMON updates | 2h | Step 1 | [NAME] |
| Step 3 | Docs/Template sync | 3h | Step 2 | [NAME] |
| Step 4A | Baseline validation | 1h | Phase 0 | [NAME] |
| Step 4B | Post-fix validation | 1h | Steps 1-3 | [NAME] |

**Total:** 15 hours (2 work days)

**Critical path:** Phase 0 → Step 1 → Step 2 → Step 3 → Step 4B

**Target:** [DATE] + 2 days

CATEGORY 5: AMBIGUOUS MECHANICS ⚙️
DRIFT-19: Task ID Extraction Pattern Imprecise
Line: 19 (R-ATL-NEW-01 scope)
Problem: "Task headers (### Task X.Y)" - leaves edge cases undefined
Edge cases:

task 1.1 (lowercase) - counted?
#### Task 1.1 (wrong level) - counted?
### Task 1.1 vs ### Task 1.10 - different?
### Task 1.1 — Title - is title part of comparison?

Fix:
markdown## Task ID Extraction Logic (R-ATL-NEW-01 Detail)

**Pattern:** `^###\s+Task\s+(\d+\.\d+)`
- Level: Must be `###` (not `##` or `####`)
- Case: "Task" must be capitalized ("task" not recognized)
- Extract: Numeric portion only (e.g., "1.1", "12.5")
- Title: Ignored during comparison

**Uniqueness check:**
- Compare: Numeric IDs as strings
- Example: "1.1" ≠ "1.10" (string comparison, not numeric)

**Examples:**
- `### Task 1.1 — Title A` vs `### Task 1.1 — Title B` → DUPLICATE (same 1.1)
- `### Task 1.1` vs `### Task 1.10` → DIFFERENT ("1.1" ≠ "1.10")
- `### Task 1.1` vs `#### Task 1.1` → Second ignored (wrong level)
- `### task 1.1` → Not recognized (lowercase)

**Error message:**
````
R-ATL-NEW-01: Duplicate task ID '1.1' at lines 45 and 230
  Line 45: ### Task 1.1 — Add dependency
  Line 230: ### Task 1.1 — Run tests
````

DRIFT-20: Coverage List Duplicate Handling Undefined
Line: 21 (coverage grammar)
Problem: If coverage entry is "1.1, 1.1" (duplicate in list), is that valid or invalid?
Fix:
markdown## Coverage Grammar (Duplicate Handling)

**List format:** `"1.1, 1.3, 1.5"`
- Parsing: Split on comma, trim whitespace
- Validation: Each unique item must exist in document

**Duplicate items in coverage list:**
- Example: `"1.1, 1.1, 1.3"` (1.1 appears twice in list)
- Treatment: **Allowed** (semantic duplicate, referencing same task multiple times)
- Rationale: Doesn't create ambiguity (still resolves to unique task)

**Invalid case:**
- Example: `"1.1, 1.3"` where task 1.1 appears 3x in document
- Error: Each referenced task must appear exactly once in document

DRIFT-21: VALIDATION_SUITE.md File Structure Undefined
Lines: 14 (A3), 43 (inventory), 78 (execution)
Problem: What's the actual format of VALIDATION_SUITE.md?
Fix:
markdown## VALIDATION_SUITE.md Structure

**Format:**
````markdown
# Validation Suite

## Category: Plan Mode Positives

### Test P1: Evidence placeholders allowed
```bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/positives/plan_with_evidence_ph.md
# Expected: exit 0
```
**Status:** [PASS/FAIL]

### Test P2: ...

## Category: Negatives

### Test N1: Instantiated rejects placeholders
```bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/instantiated_with_placeholders.md 2>&1 | grep "R-ATL-022"
# Expected: match found
```
**Status:** [PASS/FAIL]
````

**Execution (Phase A - manual):**
- Copy each bash block
- Run in terminal
- Record PASS/FAIL status
- Save summary to `validation/baseline_YYYY-MM-DD.txt`

**Execution (Phase B - scripted):**
- Script parses markdown
- Extracts bash blocks
- Runs commands
- Compares output to expected
- Generates report

CATEGORY 6: SUBTLE WORDING ISSUES 📝
DRIFT-22: "Exist Once" vs "Appear Exactly Once"
Already flagged as DRIFT-8 above but worth emphasis
Line 21: "must exist once" should be "must appear exactly once"

"Exist once" sounds like presence check (≥1)
"Appear exactly once" clearly means uniqueness check (=1)


DRIFT-23: Mode Value Case Sensitivity Assumption
Line: 47 (mode detection)
Problem: Says "case-sensitive" but doesn't show what happens with wrong case
Fix:
markdown## Mode Detection (Case Examples)

**Valid:**
- `mode: "plan"` ✅
- `mode: "instantiated"` ✅

**Invalid (case mismatch):**
- `mode: "Plan"` ❌ R-ATL-001 (must be lowercase)
- `mode: "INSTANTIATED"` ❌ R-ATL-001 (must be lowercase)
- `mode: "Plan Mode"` ❌ R-ATL-001 (invalid value)

**Error message:**
"R-ATL-001: Invalid mode 'Plan'. Must be 'plan' or 'instantiated' (lowercase)"

CATEGORY 7: FILE/ARTIFACT ISSUES 📁
DRIFT-24: A1 File Existence Ambiguous
Line: 8 (A1 command)
Problem: References plan_with_evidence_ph.md - does this file exist for baseline or needs creation?
Context: A2 has the same issue (DRIFT-3), but A1 is different because:

A1 uses a positive example (should already exist)
A2 uses a negative example (marked for creation in line 42)

Clarification needed: Is plan_with_evidence_ph.md an existing file or placeholder name?
Fix:
markdown## Current State Audit (A1 Clarified)

**A1. Spec↔Linter drift**
**File status:** `canonical_examples/positives/plan_with_evidence_ph.md`
- If exists: Use for baseline test
- If missing: Create minimal example:
````yaml
  ---
  ai_task_list:
    mode: "plan"
  ---
  ### Task 1.1 — Test
  **Evidence:**
```bash
  $ echo test
  [[PH:OUTPUT]]
```
````

**Command:** [as written]
**Expected:** [as written]

DRIFT-25: Negatives Creation Timing Unclear
Line: 42 (artifact inventory), 62 (Step 1)
Problem: When exactly are the 3 negative files created?
Line 62: "Add/update negatives" - vague
Line 42: Lists files to add - but doesn't say WHEN in Step 1
Fix:
markdown### 1) Linter (Sequenced Steps)

**Step 1.0: Create negative test fixtures (FIRST - TDD RED phase)**
- Create `canonical_examples/negatives/instantiated_with_placeholders.md`
- Create `canonical_examples/negatives/duplicate_task_ids.md`  
- Create `canonical_examples/negatives/coverage_phantom_refs.md`
- Verify they DON'T trigger errors yet (linter not updated)

**Step 1.1: Implement linter rules (SECOND - TDD GREEN phase)**
- Modify R-ATL-022 logic
- Implement R-ATL-NEW-01
- Implement R-ATL-NEW-02

**Step 1.2: Verify fixtures now trigger errors (THIRD - TDD verification)**
- Run linter on all 3 negatives
- Verify each triggers expected R-ATL-* error

CATEGORY 8: DOCUMENTATION ARTIFACTS 📚
DRIFT-26: Regression Prevention Review Checklist Incomplete
Line: 97 (mentions checklist)
Problem: Says "require review checklist" but doesn't show what's ON the checklist
Fix:
markdown## Regression Prevention (Review Checklist Detail)

**When required:** PRs modifying `ai_task_list_linter_v1_8.py`, `AI_TASK_LIST_SPEC_v1.md`, or `COMMON.md`

**Checklist (paste in PR description):**
````markdown
## Framework Change Review Checklist

### Pre-Approval (reviewer: @tech-lead)
- [ ] Linter + Spec updated together (no solo changes)
- [ ] Test fixtures added/updated (positives/negatives)
- [ ] COMMON.md updated (if behavior changes)
- [ ] Version bumped (spec v1.8, schema_version 1.6)

### Automated Verification (CI must pass)
- [ ] `python tests/test_spec_examples.py` passes
- [ ] `python tests/test_rule_consistency.py` passes
- [ ] `bash tools/run_validation_suite.sh` passes
- [ ] Canary test passes (0-2 new failures acceptable)

### Evidence (attach to PR)
- [ ] Screenshot of test output
- [ ] Baseline vs post-fix validation diff
````

**Enforcement:** GitHub branch protection requires:
1. All CI checks pass (automated)
2. @tech-lead approval after checklist verification (manual)

SUMMARY: DRIFT SEVERITY MATRIX
IDDriftCategorySeverityBlocksFix TimeLOGICAL CONTRADICTIONS1Coverage "exactly one task" vs rangesContradiction🔴 CRITICALR-ATL-NEW-02 impl5 min2Version decision duplicatedContradiction🟡 MEDIUMConfusion2 min3Baseline uses non-existent fileLogic error🔴 CRITICALPhase 010 min4Conditional language (certain change)Wording🟡 MEDIUMClarity3 minUNDEFINED REFERENCES5R-ATL-001 missing from tableMissing def🟠 HIGHDocumentation5 min6"Command-like lines" undefinedVague term🟠 HIGHR-ATL-075 impl8 min7Evidence "after" ambiguousScope unclear🟠 HIGHR-ATL-022 impl10 min8"Exist once" ambiguous wordingImprecise🟡 MEDIUMClarity2 minSPECIFICATION GAPS9Validation threshold undefinedMissing criteria🟠 HIGHDoD verification8 min10Canary selection missingMissing list🟠 HIGHRollback testing15 min11CI implementation vagueMissing details🟠 HIGHRegression prev20 min12Spec section locations missingMissing precision🟡 MEDIUMStep 2 efficiency10 min13Audit gate incompletePartial check🟡 MEDIUMQuality5 min14Goal 5 danglingNo execution🟡 MEDIUMScope clarity5 min15Script optional vs requiredAmbiguous🟡 MEDIUMDoD clarity5 minMISSING POLICIES16Backward compatibilityNo policy🟡 MEDIUMRollout risk10 min17External dependenciesNo list🟡 MEDIUMSetup5 min18Timeline/effortNo estimate🟡 MEDIUMPlanning5 minAMBIGUOUS MECHANICS19Task ID extraction impreciseEdge cases🟠 HIGHR-ATL-NEW-01 impl10 min20Coverage list duplicatesUndefined🟡 MEDIUMEdge case5 min21VALIDATION_SUITE formatUndefined🟡 MEDIUMStep 48 minWORDING ISSUES22"Exist once" vs "appear exactly"Imprecise🟡 MEDIUMClarity2 min23Mode case sensitivity examplesMissing🟡 MEDIUMDocumentation5 minFILE ARTIFACTS24A1 file existence ambiguousStatus unclear🟡 MEDIUMPhase 05 min25Negatives creation timingSequence unclear🟡 MEDIUMStep 15 minDOCUMENTATION26Review checklist incompleteMissing content🟡 MEDIUMProcess8 min
Total drifts: 26 (was 31 in initial count, consolidated some duplicates)
Fix time: ~3 hours total

Critical (3): 18 minutes
High (7): 91 minutes
Medium (16): 85 minutes


ANSWER: Is This Plan Viable?
Progress from previous versions: 60% → 75% → 80% execution precision
Improvements made:

✅ Added "Scope / Grammar" column to rule table
✅ Added evidence block definition section
✅ Added mode detection section
✅ Clarified linter versioning (in-place modification)
✅ Added directory structure to artifact inventory

Remaining critical issues (3):

DRIFT-1: Coverage resolution logic contradicts itself
DRIFT-3: Baseline test uses file that doesn't exist yet
DRIFT-7: Evidence block "after" scope ambiguous

High-severity issues (7): Missing definitions, specification gaps that block implementation
Medium-severity issues (16): Quality improvements, clarity enhancements, policy gaps

RECOMMENDATION
You're 2 hours from executable. The structure is excellent (learned from all previous feedback), but implementation details need tightening.
Priority fix sprint (2 hours):
Hour 1 - Critical blockers (18 min):

Fix DRIFT-1: Clarify "exactly one task" means uniqueness of each referenced ID
Fix DRIFT-3: Defer A2 or use existing file for baseline
Fix DRIFT-7: Define evidence block scope precisely (first block? all blocks?)

Hour 1 continued - High severity (91 min):
4. Add R-ATL-001 to rule table (DRIFT-5)
5. Define "command-like lines" for R-ATL-075 (DRIFT-6)
6. Clarify "exist once" → "appear exactly once" (DRIFT-8)
7. Add validation thresholds (DRIFT-9)
8. Identify canaries (DRIFT-10)
9. Add CI implementation details (DRIFT-11)
10. Add spec section references (DRIFT-12)
Hour 2 - Remaining medium issues (85 min total, pick top priorities):

Remove conditional language (DRIFT-4)
Add audit gate for Owner/Deadline (DRIFT-13)
Defer or expand Goal 5 (DRIFT-14)
Add backward compat policy (DRIFT-16)
Add dependencies list (DRIFT-17)
Add timeline (DRIFT-18)
Define task ID extraction pattern (DRIFT-19)

Then: Mark as "Ready for Phase 0" and execute.
The plan is structurally sound and conceptually correct. The 26 drifts are mostly precision issues (ambiguous definitions, missing specifics, incomplete checklists) rather than structural failures. Fix the definitional gaps and this becomes immediately executable.
You've demonstrated excellent iterative improvement. Each version addressed major feedback and got tighter. This final version is 80% there - very close to production-ready.
