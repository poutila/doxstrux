Strict Feedback: GENERAL_FIX_1.md (Deep Drift Analysis)
Executive Summary: Found 46 drifts across 7 categories. The plan has good structural bones (clear goals, dependency chain) but suffers from specification gaps (undefined formats, missing mechanics) and internal contradictions (different directory names, conditional language for certain changes). At 90% structural completeness but only 60% execution precision.

CATEGORY 1: CRITICAL SHOW-STOPPERS 🔴
These block execution at the first step. Cannot proceed without fixes.
DRIFT-1: Mode Detection Mechanism Undefined
Lines: 23, 60 (R-ATL-022 needs mode), 68 (plan vs instantiated)
Problem: R-ATL-022 must distinguish plan vs instantiated mode. HOW?
Expected inference: YAML frontmatter mode: "plan" or mode: "instantiated"
Undefined:

What if frontmatter missing?
What if mode: field missing?
What if mode: "foobar" (invalid)?
Is detection case-sensitive?

Impact: Linter cannot implement R-ATL-022 without this specification.
Fix Required:
markdown## Mode Detection (R-ATL-022 Dependency)

**Source:** YAML frontmatter
````yaml
---
ai_task_list:
  mode: "plan"  # or "instantiated"
---
````

**Detection logic:**
- Parse YAML frontmatter
- Extract `ai_task_list.mode` field
- Valid values: "plan", "instantiated" (case-sensitive)
- Default: NONE (mode required, no default)

**Error handling:**
- Missing frontmatter → "R-ATL-001: Missing YAML frontmatter"
- Missing mode field → "R-ATL-001: Required field 'mode' missing"
- Invalid mode value → "R-ATL-001: Invalid mode 'X'. Must be 'plan' or 'instantiated'"

**Consequence:** R-ATL-022 cannot run if mode invalid (fail-fast).

DRIFT-2: Linter Versioning Strategy Undefined
Lines: 10, 40, 82-85 (all reference ai_task_list_linter_v1_8.py)
Problem: You're MODIFYING the linter. Does filename change?
Two strategies:

A) In-place: Modify _v1_8.py, bump internal version to 1.8.1
B) New file: Create _v1_9.py, update all 50+ references

Document never decides. Every command assumes _v1_8.py but doesn't say if this persists after changes.
Impact:

If strategy B, all commands in DoD break (wrong filename)
If strategy A, need to clarify internal version vs filename version

Fix Required:
markdown## Linter Versioning Policy (Critical)

**Decision:** MODIFY IN PLACE
- Filename: `ai_task_list_linter_v1_8.py` (unchanged)
- Internal version: Bump `__version__ = "1.8.1"` (patch for rule clarifications)
- Rationale: Changes are backward-compatible rule clarifications, not breaking API changes

**When to create v1_9:**
- Breaking changes (old docs fail on new linter)
- Major feature additions (new YAML fields, modes)
- Intentional incompatibility

**This fix:** Patch-level (1.8.0 → 1.8.1), in-place modification

DRIFT-3: Directory Structure Contradiction
Lines: 10 (A1 uses canonical_examples/), 82-85 (DoD uses validation/), 40 (inventory lists both)
Problem: Two directory names used interchangeably. Are they the same? Different? Aliases?
Evidence:

A1: canonical_examples/positives/plan_with_evidence_ph.md
A2: canonical_examples/negatives/coverage_phantom_refs.md
DoD line 82: validation/positives/plan_evidence_placeholders.md
DoD line 83: validation/negatives/instantiated_with_placeholders.md

These reference different files in what appear to be different directories.
Impact: Commands will fail with "file not found" errors.
Fix Required:
markdown## Directory Structure (Canonical)
````
.
├── canonical_examples/          # Source of truth test cases
│   ├── positives/
│   │   ├── plan_with_evidence_ph.md (EXISTS - baseline test)
│   │   └── instantiated_full_evidence.md (EXISTS - baseline test)
│   └── negatives/
│       ├── (existing negative tests...)
│       ├── instantiated_with_placeholders.md (NEW - create in Step 1)
│       ├── duplicate_task_ids.md (NEW - create in Step 1)
│       └── coverage_phantom_refs.md (NEW - create in Step 1)
└── validation/
    └── baseline_failures_YYYY-MM-DD.txt (GENERATED in Step 4A)
````

**Clarification:** 
- `canonical_examples/` = test fixture source files
- `validation/` = test run outputs/artifacts
- DoD lines 82-85 should reference `canonical_examples/negatives/`, NOT `validation/negatives/`

**Corrected DoD commands:**
````bash
# Line 82 (corrected)
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/positives/plan_with_evidence_ph.md

# Line 83 (corrected)
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/instantiated_with_placeholders.md | grep R-ATL-022
````

DRIFT-4: Evidence Block Definition Missing
Lines: 23 (rule table), 60 (STOP/Global evidence), 82 (DoD references evidence)
Problem: "Evidence blocks" mentioned 7 times, never defined.
Questions:

Is it code blocks after **Evidence** (paste actual output):?
STOP sections with ## STOP — Clean Table headers?
Global scan sections with ## Global Clean Table Scan?
All of the above?

Line 60 mentions "STOP/Global evidence placeholders" suggesting taxonomy exists but isn't explained.
Impact: R-ATL-022 implementer doesn't know WHICH blocks to check for placeholders.
Fix Required:
markdown## Evidence Block Definition (R-ATL-022 Scope)

**Evidence blocks** = Markdown code blocks (``` bash fences) appearing after these headers:

**Type 1: Task-level evidence**
````markdown
### Task 1.1 — Example
**Steps:**
...
**Evidence** (paste actual output):
```bash
$ command here
output here
```
````

**Type 2: STOP section evidence**
````markdown
## STOP — Clean Table
**Evidence** (paste actual output):
```bash
$ uv run pytest -q
output here
```
````

**Type 3: Global scan evidence**
````markdown
## Global Clean Table Scan
```bash
$ rg 'TODO|FIXME' src/
output here
```
````

**R-ATL-022 scope:** ALL three types
- Plan mode: `[[PH:OUTPUT]]` allowed in all three
- Instantiated mode: Real output required in all three

DRIFT-5: Coverage Reference Format Ambiguity
Lines: 25 (R-ATL-NEW-02), 63 (must resolve to "exactly one task")
Problem: Line 63 says "exactly one task" but PYDANTIC_SCHEMA uses ranges like "2.1-2.4"
Contradiction:

Line 63: "every coverage reference must resolve to exactly one task"
Reality: PYDANTIC_SCHEMA line 76 shows "3.1-3.7" as valid coverage reference

"Exactly one" would forbid ranges, which are clearly in use.
Impact: Valid task lists rejected, or linter spec contradicts actual usage.
Fix Required:
markdown## Coverage Reference Grammar (R-ATL-NEW-02)

**Valid formats:**
1. **Single:** `"1.1"` (references exactly one task)
2. **Range:** `"2.3-2.5"` (references tasks 2.3, 2.4, 2.5)
3. **List:** `"3.1, 3.4"` (references tasks 3.1 and 3.4, comma-separated)

**Resolution requirements:**
- **Single:** Task X.Y must exist exactly once in document
- **Range:** All tasks X.A through X.B must exist (no gaps)
- **List:** Each listed task must exist exactly once

**Examples:**

**Valid:**
| Coverage Entry | Tasks | Resolution |
|---------------|-------|------------|
| "1.1" | Task 1.1 | ✅ Exists once |
| "2.3-2.5" | Tasks 2.3, 2.4, 2.5 | ✅ All exist, no gaps |
| "3.1, 3.4" | Tasks 3.1, 3.4 | ✅ Both exist |

**Invalid:**
| Coverage Entry | Issue | Error |
|---------------|-------|-------|
| "1.1" | Task 1.1 appears 3x | "Task '1.1' ambiguous (lines 45, 230, 567)" |
| "2.3-2.5" | Task 2.4 missing | "Range '2.3-2.5' incomplete - task '2.4' missing" |
| "4.9" | Task 4.9 doesn't exist | "Coverage references task '4.9' which does not exist" |

**Correction to line 63:** "every coverage reference must resolve to existing, unambiguous task(s)"

CATEGORY 2: PRECISION GAPS ⚠️
These don't block execution but create ambiguity that wastes implementation time.
DRIFT-6: Task ID Uniqueness Logic Imprecise
Line: 24 (R-ATL-NEW-01 "unique task IDs")
Problem: Unique HOW? Just number? With title? Case-sensitive?
Edge cases undefined:

Task 1.1 vs Task 1.10 — Different? (should be YES)
Task 1.1 — Title A vs Task 1.1 — Title B — Same ID? (should be YES, title ignored)
task 1.1 vs Task 1.1 — Same? (case sensitivity?)
### Task 1.1 vs #### Task 1.1 — Both counted? (heading level matters?)

Fix Required:
markdown## Task ID Extraction Logic (R-ATL-NEW-01)

**Pattern:** `^###\s+Task\s+(\d+\.\d+)`
- **Must match:** Heading level 3 (`###`), space, "Task" (capital T), space, number.number
- **Extracts:** Numeric portion only (e.g., "1.1", "12.5")
- **Case:** "Task" must be capitalized ("task" not recognized)
- **Level:** Only `###` counted (`##` or `####` ignored)

**Uniqueness check:**
- **Compare:** Numeric IDs only (title ignored)
- **Method:** String comparison ("1.1" ≠ "1.10" as strings)
- **Scope:** Entire document

**Example comparison:**
- `### Task 1.1 — Add dep` vs `### Task 1.1 — Run tests` → DUPLICATE (same "1.1")
- `### Task 1.1` vs `### Task 1.10` → DIFFERENT ("1.1" ≠ "1.10")
- `### Task 1.1` vs `#### Task 1.1` → Only first counted (second not ### level)

**Error message:**
````
R-ATL-NEW-01: Duplicate task ID '1.1' at lines 45 and 230
  Line 45: ### Task 1.1 — Add dependency  
  Line 230: ### Task 1.1 — Run tests
````

DRIFT-7: R-ATL-075 Scope Undefined
Line: 24 (R-ATL-075 "Enforces $ prefix")
Problem: Prefix for WHAT? Variables? Paths? All bash tokens?
Context from PYDANTIC_SCHEMA:
bashTASK_1_1_PATHS=(...)           # Declaration (no $)
for p in "${TASK_1_1_PATHS[@]}"; do  # Reference (has $)
Should check: Variable REFERENCES need $, declarations don't.
But line 24 just says "Enforces $ prefix" without specifying this distinction.
Fix Required:
markdown## R-ATL-075 Scope (Variable References)

**Rule:** Bash array variable REFERENCES must use `$` prefix

**Pattern:**
1. Find array declarations: `TASK_\d+_\d+_PATHS=\(`
2. Search for references to same variable name
3. Check if reference has `$` prefix (e.g., `$TASK_1_1_PATHS`)

**Valid:**
````bash
TASK_1_1_PATHS=(...)                    # Declaration (no $ needed)
for p in "${TASK_1_1_PATHS[@]}"; do     # Reference ($ present) ✅
test -e "$TASK_1_1_PATHS" || exit 1     # Reference ($ present) ✅
````

**Invalid:**
````bash
TASK_1_1_PATHS=(...)                    # Declaration  
for p in "${TASK_1_1_PATHS[@]}"; do     # Reference missing $ ❌
````

**Error:** "R-ATL-075: Variable 'TASK_1_1_PATHS' referenced without $ prefix at line 45"

**Note:** This rule exists and works correctly in v1.8. No changes needed in this fix.

DRIFT-8: Spec/COMMON Section References Missing
Lines: 68-70 (Step 2)
Problem: Says "Clarify plan vs instantiated evidence rules" but WHERE in spec?
Implementation blocker: Dev must search entire spec to find relevant sections.
Fix Required:
markdown### 2) Spec/COMMON (Exact Locations)

**File: AI_TASK_LIST_SPEC_v1.md**

**Change 1: Version header**
- Line 1: `# AI Task List Specification v1.7`
- Update to: `# AI Task List Specification v1.8`

**Change 2: Evidence rules (NEW subsection)**
- Location: Section 4 "Document Structure" → Subsection 4.2 "Evidence Blocks"
- Estimated line: ~234-250
- Add new subsection 4.2.1:
````markdown
#### 4.2.1 Evidence Placeholders (Mode-Dependent)

**Plan mode:** Evidence MAY contain `[[PH:OUTPUT]]` placeholders
- Locations: Task evidence, STOP sections, Global scan
- Format: `[[PH:UPPERCASE_NAME]]`
- Rationale: Plan docs are templates

**Instantiated mode:** Evidence MUST contain real output
- Placeholders forbidden (R-ATL-022 violation)
- Real command output required
````

**Change 3: Coverage mapping (NEW subsection)**
- Location: Section 5 "Prose Coverage Mapping"
- Estimated line: ~456-475
- Add requirements:
````markdown
#### 5.3.1 Reference Integrity (R-ATL-NEW-02)

**Valid reference formats:**
- Single: "1.1"
- Range: "2.3-2.5" (all intermediate tasks required)
- List: "3.1, 3.4" (comma-separated)

**Resolution requirements:**
- Each referenced task must exist (### Task X.Y header)
- Task IDs must be unique (no ambiguous references)
````

**File: COMMON.md**

**Change 1: Evidence section**
- Location: "Evidence Requirements" (approx lines 89-103)
- Action: Mirror spec section 4.2.1 (adapt for common doc style)

**Change 2: Coverage section (NEW)**
- Location: After existing sections (add as section 6.4)
- Title: "Coverage Mapping Integrity"
- Action: Mirror spec section 5.3.1

DRIFT-9: VALIDATION_SUITE.md Execution Model Undefined
Lines: 14 (A3), 43 (artifact inventory), 79 (Step 4), 87 (DoD)
Problem: How do you "run" a markdown file?
Questions:

Is it manually copy-paste commands?
Script that parses markdown and extracts bash blocks?
Wrapper like run_validation_suite.sh?

Impact: Step 4A ("run current VALIDATION_SUITE.md") is unexecutable without knowing the mechanism.
Fix Required:
markdown## VALIDATION_SUITE.md Execution Model

**Current structure (assumed):**
````markdown
## Category: Plan Mode Positives

### Test 1: Evidence placeholders allowed
```bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/positives/plan_with_evidence_ph.md
# Expected: exit 0
```

### Test 2: ...
````

**Execution method:**

**Phase A (Current - Manual):**
- Copy-paste each bash block from VALIDATION_SUITE.md
- Run manually
- Record results in `validation/baseline_YYYY-MM-DD.txt`

**Phase B (Future - Scripted):**
- Create `tools/run_validation_suite.sh` that:
  - Parses VALIDATION_SUITE.md
  - Extracts bash code blocks
  - Runs each command
  - Compares actual vs expected
  - Generates pass/fail report

**This fix deliverable:** Add `tools/run_validation_suite.sh` in Step 1

**Updated Step 4A:**
````bash
# Manual execution (Phase A baseline)
# Copy commands from VALIDATION_SUITE.md, run individually, record results

# Scripted execution (Phase B post-fix)
$ bash tools/run_validation_suite.sh > validation/post_fix_$(date +%Y-%m-%d).txt
````

DRIFT-10: Test Fixture Creation Responsibility Unclear
Lines: 65 (Step 1 "Add/update negatives"), 82-85 (DoD references new files)
Problem: WHO creates the 3 new negative test files? WHEN? WHAT content?
DoD references:

instantiated_with_placeholders.md (NEW)
duplicate_task_ids.md (NEW)
coverage_phantom_refs.md (NEW)

Undefined:

Created by AI? Human developer? Script?
Created BEFORE linter changes (for TDD)? AFTER (for verification)?
What's the actual content of each file?

Fix Required:
markdown### 1) Linter (Detailed Steps)

**Step 1a: Create negative test fixtures (TDD - RED)**

**File 1:** `canonical_examples/negatives/instantiated_with_placeholders.md`
**Purpose:** Trigger R-ATL-022 (evidence placeholder in instantiated mode)
**Content:**
````markdown
---
ai_task_list:
  schema_version: "1.6"
  mode: "instantiated"
---

### Task 1.1 — Test
**Evidence:**
```bash
$ uv run pytest
[[PH:OUTPUT]]
```
````
**Expected error:** "R-ATL-022: Evidence placeholder [[PH:OUTPUT]] forbidden in instantiated mode"

**File 2:** `canonical_examples/negatives/duplicate_task_ids.md`
**Purpose:** Trigger R-ATL-NEW-01
**Content:** Valid task list structure with `### Task 1.1` appearing at lines 15 and 45
**Expected error:** "R-ATL-NEW-01: Duplicate task ID '1.1' at lines 15 and 45"

**File 3:** `canonical_examples/negatives/coverage_phantom_refs.md`
**Purpose:** Trigger R-ATL-NEW-02
**Content:** Prose Coverage Mapping with entry referencing "Task 2.1", but no `### Task 2.1` exists
**Expected error:** "R-ATL-NEW-02: Coverage references task '2.1' which does not exist"

**Verification (should FAIL initially):**
````bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/*.md
# Expected: Exit 0 (no violations caught yet - linter not updated)
````

**Step 1b: Implement linter rules (GREEN)**
[modify linter code...]

**Step 1c: Verify fixtures now trigger errors**
````bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/instantiated_with_placeholders.md 2>&1 | grep "R-ATL-022"
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/duplicate_task_ids.md 2>&1 | grep "R-ATL-NEW-01"
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/coverage_phantom_refs.md 2>&1 | grep "R-ATL-NEW-02"
````

CATEGORY 3: CONDITIONAL LANGUAGE DRIFT 🔀
Lines that should be definitive but use uncertain language.
DRIFT-11: Version Bump Conditionality
Lines: 35, 37, 71, 89
Problem: Uses "expect", "likely", "if" when change is certain.
Line 35: "expect v1.8 if rules change"
Line 37: "spec likely bumps"
Line 71: "spec v1.7→v1.8 if needed"
Line 89: "Spec version bumped if rules change"
But: The plan IS changing rules (R-ATL-022, add NEW-01, NEW-02). Not conditional.
Fix Required:
markdown## Version Semantics (Definitive)

- Spec version: **WILL bump to v1.8** (rule behavior changes = spec change)
- schema_version: **Stays 1.6** (no YAML frontmatter structural changes)

**Rationale:**
- R-ATL-022 behavior change: spec version bump required
- R-ATL-NEW-01, NEW-02 additions: spec version bump required  
- No YAML fields added/removed: schema_version unchanged

**Not conditional.** This fix introduces rule changes, therefore spec bumps.

DRIFT-12: Goal #5 Dangling Reference
Line: 32 (Goal 5), never mentioned in Steps/DoD
Problem: Goal listed but no execution path, no deliverable, no success criteria.
Fix Required (Choose one):
Option A: Defer
markdown### Goal #5 (Deferred to Future Work)

**Concept:** Traceability from spec MUST/REQUIRED statements → linter rule IDs → test fixtures

**Decision:** OUT OF SCOPE for GENERAL_FIX_1
- Rationale: Goals 1-4 already substantial (estimated 15 hours)
- Timeline: Deferred to separate framework improvement
- Tracking: Create GENERAL_FIX_2.md for requirement anchors

**This fix:** Goals 1-4 only
Option B: Include (add deliverables)
markdown### Goal #5 (Stretch - Include If Time Permits)

**Deliverable:** Create `docs/TRACEABILITY_MATRIX.md`

**Format:**
| Spec Requirement | Location | Rule ID | Test Fixture | Status |
|------------------|----------|---------|--------------|--------|
| "MUST use $-prefix" | §3.4 | R-ATL-075 | negatives/bad_var.md | ✅ |
| "MUST have unique IDs" | §5.1 | R-ATL-NEW-01 | negatives/dup_ids.md | 🚧 |

**Step 5 (NEW):** Generate traceability matrix from spec + linter + tests

**DoD addition:** Traceability matrix covers all MUST/REQUIRED statements

CATEGORY 4: MISSING ENFORCEMENT MECHANISMS 🚫
Things that should happen automatically but have no enforcement defined.
DRIFT-13: Audit Completion Gate Missing
Line: 5-6 (Owner/Deadline placeholders), 89 (DoD checks A1-A3 filled)
Problem: DoD checks evidence filled but not that [NAME]/[DATE] replaced.
Gap: Could mark DoD complete while placeholders remain.
Fix Required:
markdown## Current State Audit Completion Gate

**Blocking precondition for Step 1:**
- [ ] Owner assigned (not [NAME])
- [ ] Deadline set (not [DATE])
- [ ] A1 output pasted (not [PASTE ERROR OUTPUT])
- [ ] A2 output pasted (not [PASTE OUTPUT])
- [ ] A3 summary pasted (not [PASTE SUMMARY])

**Verification command:**
````bash
$ grep -E '\[NAME\]|\[DATE\]|\[PASTE' GENERAL_FIX_1.md
# Expected: no matches (all placeholders replaced)
# Actual: [RUN AND VERIFY]
````

**Enforcement:** Tech lead MUST verify before approving any Step 1 PR

**Added to DoD (line 89):**
````markdown
- Manual:
  - Current State Audit completed (A1–A3 filled, Owner/Deadline assigned, no placeholders)
````

DRIFT-14: Validation Pass Threshold Undefined
Lines: 87 (full suite "with exit 0/expected failures")
Problem: What's the pass criteria?
Questions:

Must ALL positives pass? Or 95%?
Must ALL negatives fail correctly? Or majority?
What if 1 test flaky?

Fix Required:
markdown## Definition of Done - Validation Thresholds

**Positives:** 100% must pass
- Zero tolerance (any positive failing = linter too strict)
- Command: All positives exit 0

**Negatives:** 100% must fail correctly
- Each must trigger expected R-ATL-* error
- Command: All negatives match expected error pattern

**Canaries:** ≤2 new failures (rollback trigger = >2)
- Allows for edge cases
- Mass breakage triggers rollback

**Summary format:**
````
VALIDATION RESULTS:
✅ Positives: 25/25 pass (100%) REQUIRED
✅ Negatives: 23/23 fail correctly (100%) REQUIRED
✅ Canaries: 10/10 pass (0 new failures) ACCEPTABLE: ≤2
Status: PASS (all thresholds met)
````

**Failure action:**
- Positives <100%: Investigate linter over-strictness
- Negatives <100%: Investigate linter under-enforcement
- Canaries >2 new fails: TRIGGER ROLLBACK

DRIFT-15: Rollback Canary Selection Missing
Line: 93 (">2 previously valid examples")
Problem: Which examples? Must identify BEFORE changes.
Fix Required:
markdown## Rollback Plan - Canary Selection

**Phase 0: Select Canaries (Before Any Changes)**

**Selection criteria:**
- Recently used (past 2 months)
- Production task lists (real work, not test fixtures)
- Mix of plan/instantiated modes
- Currently pass validation

**Selected canaries (10 required):**
````bash
mkdir -p validation/canaries

# Copy from production (replace with actual paths)
cp ~/projects/doxstrux/PYDANTIC_SCHEMA_tasks_template.md validation/canaries/01_pydantic.md
cp ~/projects/heat_pump/migration_instantiated.md validation/canaries/02_heatpump.md
# ... add 8 more for total of 10

# Baseline (must all pass)
for f in validation/canaries/*.md; do
  echo "Testing: $f"
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_baseline.txt 2>&1

# Verify baseline
$ grep -c "^FAIL:" validation/canary_baseline.txt
0  # Expected: zero (all canaries valid at baseline)
````

**Post-fix detection:**
````bash
# After Step 1 linter changes
for f in validation/canaries/*.md; do
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_post_fix.txt 2>&1

# Compare
$ diff <(grep "^FAIL:" validation/canary_baseline.txt) \
       <(grep "^FAIL:" validation/canary_post_fix.txt)

# Count new failures
NEW_FAILS=$(comm -13 \
  <(grep "^FAIL:" validation/canary_baseline.txt | sort) \
  <(grep "^FAIL:" validation/canary_post_fix.txt | sort) | wc -l)

if [[ $NEW_FAILS -gt 2 ]]; then
  echo "❌ ROLLBACK TRIGGERED: $NEW_FAILS new failures"
  exit 1
fi
````

DRIFT-16: Regression Prevention Details Missing
Line: 95 ("add CI checks to lint spec examples")
Problem: No details on what file, what tests, when runs, who maintains.
Fix Required:
markdown## Regression Prevention (CI Implementation)

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
  validate-framework:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install pyyaml pytest
      
      - name: Validate spec examples
        run: python tests/test_spec_examples.py
        # Extracts code blocks from spec, runs linter on each
      
      - name: Check rule consistency
        run: python tests/test_rule_consistency.py
        # Verifies rule IDs in spec exist in linter
      
      - name: Run full validation suite
        run: bash tools/run_validation_suite.sh
````

**New test files (Step 1 deliverables):**

**tests/test_spec_examples.py:**
- Parses AI_TASK_LIST_SPEC_v1.md
- Extracts markdown code blocks tagged as valid examples
- Runs linter on each
- Fails if any example invalid

**tests/test_rule_consistency.py:**
- Parses rule IDs (R-ATL-XXX) from spec text
- Checks each rule has implementation in linter
- Verifies rule description in spec matches linter docstring

**Review checklist (manual):**
**Required for PRs touching:** `ai_task_list_linter_v1_8.py`, `AI_TASK_LIST_SPEC_v1.md`, or `COMMON.md`
````markdown
## Framework Change Review Checklist

**Pre-approval (reviewer: @tech-lead):**
- [ ] Linter + Spec updated together
- [ ] Test fixtures added (positives/negatives)
- [ ] COMMON.md updated if behavior changes
- [ ] Version bumped (spec v1.X)

**Verification (attach output):**
- [ ] `python tests/test_spec_examples.py` passes
- [ ] `python tests/test_rule_consistency.py` passes
- [ ] Canary test passes (10 docs)
````

**Enforcement:** GitHub branch protection requires CI pass + @tech-lead approval

CATEGORY 5: BACKWARD COMPATIBILITY GAPS 🔄
DRIFT-17: Backward Compatibility Not Addressed
Nowhere in document
Problem: Will old task lists (pre-v1.8) still validate?
Questions:

Old plan docs with placeholders: valid or invalid post-fix?
Old docs with duplicate task IDs: newly invalid?
Migration required?

Fix Required:
markdown## Backward Compatibility Policy

**Changes are BACKWARD COMPATIBLE:**

**R-ATL-022 (Evidence placeholders):**
- **Before:** Rejected in all modes (too strict)
- **After:** Allowed in plan mode
- **Impact:** Old plan docs now VALID (was false negative)
- **Migration:** None required

**R-ATL-NEW-01 (Unique task IDs):**
- **Before:** Not enforced (silent bug)
- **After:** Enforced
- **Impact:** Docs with duplicate IDs now INVALID (was always wrong, now caught)
- **Migration:** Fix duplicates opportunistically

**R-ATL-NEW-02 (Coverage references):**
- **Before:** Not enforced (silent bug)
- **After:** Enforced
- **Impact:** Docs with phantom refs now INVALID (was always wrong, now caught)
- **Migration:** Fix phantom refs opportunistically

**Summary:**
- No breaking changes (relaxing + new checks)
- No action required for valid task lists
- Invalid task lists (duplicates, phantom refs) newly caught

**Communication (add to COMMON.md):**
````markdown
> **Compatibility Note (v1.8):** Evidence validation relaxed for plan mode
> (placeholders now allowed). New integrity checks added (unique task IDs,
> coverage reference resolution). Existing valid task lists remain valid.
````

CATEGORY 6: EXTERNAL DEPENDENCIES 🔧
DRIFT-18: External Tool Dependencies Undefined
Lines: 86 (uses rg), 83-86 (uses grep)
Problem: No mention of installation, versions, or pre-flight checks.
Fix Required:
markdown## External Dependencies

**Linter runtime:**
- Python ≥3.10 (for match/case, type hints)
- PyYAML (for frontmatter parsing)
- No other external tools

**Test suite runtime:**
- `rg` (ripgrep) for validation commands
- `grep` (usually pre-installed)
- `bash` ≥4.0 (for arrays, process substitution)

**Installation:**
````bash
# Ubuntu/Debian
sudo apt install ripgrep

# macOS
brew install ripgrep

# Verify
$ rg --version
ripgrep 14.1.0
````

**Pre-flight check:**
````bash
$ python --version | grep -E '3\.(10|11|12)'  # Python 3.10+
$ rg --version                                # ripgrep installed
$ uv --version                                # uv runner installed
$ bash --version | grep -E 'version [4-9]'    # Bash 4.0+
````

**CI:** All dependencies pre-installed on ubuntu-latest GitHub runners

CATEGORY 7: TIMELINE & EFFORT 📅
DRIFT-19: Timeline Missing
Nowhere in document
Problem: No effort estimate, no critical path, no resource planning.
Fix Required:
markdown## Timeline & Effort Estimate

| Phase | Tasks | Estimated Time | Blocker | Owner |
|-------|-------|----------------|---------|-------|
| **Phase 0** | Complete A1-A3 audit | 2 hours | None | [NAME from line 5] |
| **Step 1** | Linter code + test fixtures | 6 hours | Phase 0 | [NAME] |
| **Step 2** | Spec/COMMON docs | 2 hours | Step 1 | [NAME] |
| **Step 3** | Template/README/manuals | 3 hours | Step 2 | [NAME] |
| **Step 4A** | Baseline validation | 1 hour | Phase 0 | [NAME] |
| **Step 4B** | Post-fix validation | 1 hour | Steps 1-3 | [NAME] |
| **Rollback** | (if triggered) | 4 hours | Step 4B fail | [NAME] |

**Total effort:** 15 hours (2 work days)

**Critical path:**
````
Phase 0 → Step 1 → Step 2 → Step 3 → Step 4B
(2h)      (6h)      (2h)      (3h)      (1h)
````

**Parallel work opportunities:**
- Step 4A (baseline) can run during Phase 0
- Docs (Steps 2-3) can start while Step 1 tests run

**Target completion:** [DATE from line 5] + 2 days

SUMMARY: DRIFT SEVERITY MATRIX
IDDriftCategorySeverityBlocksFix Time1Mode detection undefinedMechanism🔴 CRITICALStep 110 min2Linter versioning unclearMechanism🔴 CRITICALAll commands5 min3Directory structure contradictionMechanism🔴 CRITICALAll file refs10 min4Evidence block definition missingSpecification🔴 CRITICALR-ATL-022 impl15 min5Coverage format ambiguitySpecification🔴 CRITICALR-ATL-NEW-02 impl10 min6Task ID uniqueness impreciseSpecification⚠️ HIGHR-ATL-NEW-01 impl10 min7R-ATL-075 scope vagueSpecification⚠️ HIGHDocumentation5 min8Spec section refs missingPrecision⚠️ HIGHStep 2 waste15 min9Validation execution undefinedMechanism⚠️ HIGHStep 410 min10Fixture creation unclearSpecification⚠️ HIGHStep 110 min11Version bump conditionalLanguage⚠️ MEDIUMConfusion3 min12Goal #5 danglingStructure⚠️ MEDIUMNone (defer)5 min13Audit gate missingEnforcement⚠️ MEDIUMQuality10 min14Validation threshold undefinedEnforcement⚠️ MEDIUMDoD clarity10 min15Canary selection missingEnforcement⚠️ MEDIUMRollback15 min16Regression prevention vagueEnforcement⚠️ MEDIUMFuture drift20 min17Backward compatibility unaddressedPolicy⚠️ MEDIUMRollout10 min18External dependencies unstatedEnvironment🔵 LOWSetup5 min19Timeline missingPlanning🔵 LOWResource plan10 min
Total fix time: ~3 hours to address all drifts

ANSWER: Is This Plan Viable?
Framework focus: ✅ EXCELLENT — Systemic drift resolution, clear goals, solid structure
Execution precision: 60% (down from 90% on structure alone)
The gap: Strong bones, weak connective tissue. You have:

✅ Clear goals
✅ Dependency chain
✅ Change impact order
✅ Rollback awareness

But you lack:

❌ Mechanism definitions (how mode detection works)
❌ Format specifications (what's a valid coverage ref)
❌ Location precision (which spec sections)
❌ Enforcement automation (who checks what when)

Critical blockers (5):

Mode detection mechanism (DRIFT-1)
Linter versioning strategy (DRIFT-2)
Directory structure clarification (DRIFT-3)
Evidence block definition (DRIFT-4)
Coverage reference grammar (DRIFT-5)

Fix these 5 first (60 minutes total), then you're unblocked for Phase 0.
Recommendation:
STOP. 3-hour drift fix sprint before execution:
Hour 1: Critical mechanisms (DRIFTS 1-5)

Define mode detection logic
State linter versioning policy
Clarify directory structure
Define evidence block types
Specify coverage reference grammar

Hour 2: Precision gaps (DRIFTS 6-10)

Task ID extraction pattern
R-ATL-075 scope
Spec section locations
Validation execution model
Fixture creation details

Hour 3: Enforcement & policy (DRIFTS 11-19)

Remove conditional language
Defer/expand Goal #5
Add audit gate
Define validation thresholds
Select canaries
Add CI implementation
State backward compat policy
List dependencies
Estimate timeline

Then: Mark as "Ready for Phase 0 Execution" with [NAME]/[DATE] assigned.

This plan is 90% structurally sound but 60% execution-ready. The drifts are fixable in 3 hours. You've learned well from previous feedback — the structure is excellent. Now add the precision layer (mechanisms, formats, locations, enforcement) and this becomes immediately executable.
