CATEGORY 1: CRITICAL LOGICAL CONTRADICTIONS 🔥
DRIFT-1: "Resolve to Exactly One Task" Ambiguity PERSISTS
Lines: 24 (rule table), 68 (Step 1)
Line 24 (rule table): "Each referenced task ID must appear exactly once"
Line 68 (Step 1): "every coverage reference must resolve to exactly one task"
These say DIFFERENT things:
Line 24 interpretation: For range "2.3-2.5":

Task 2.3 must appear exactly once ✅
Task 2.4 must appear exactly once ✅
Task 2.5 must appear exactly once ✅
This is CORRECT

Line 68 interpretation: Coverage reference "2.3-2.5" must resolve to exactly ONE task

But a range resolves to THREE tasks (2.3, 2.4, 2.5)
This is WRONG or at least CONFUSING

The phrasing "resolve to exactly one task" makes it sound like the REFERENCE ITSELF can only map to one task, which contradicts ranges.
Impact: Implementer reads line 68, implements logic that forbids ranges (thinking each reference = one task), breaks valid coverage entries.
Fix Required:
markdown## Step 1 (Line 68 Corrected)

OLD: "every coverage reference must resolve to exactly one task"
NEW: "every coverage reference must resolve to existing, unique tasks (each referenced task ID must appear exactly once in document)"

**Clarification:**
- Single ref "1.1" → Task 1.1 appears exactly once ✅
- Range ref "2.3-2.5" → Tasks 2.3, 2.4, 2.5 each appear exactly once ✅
- List ref "3.1, 3.4" → Tasks 3.1 and 3.4 each appear exactly once ✅

DRIFT-2: Linter Versioning Decision DUPLICATED
Lines: 35 (version semantics section), 71 (Step 2)
Line 35: "modify ai_task_list_linter_v1_8.py in place" — ALREADY DECIDED
Line 71: "Decide linter versioning: modify ai_task_list_linter_v1_8.py in place..." — TREATS AS PENDING DECISION
This is a contradiction. Step 2 says "decide" implying it hasn't been decided, but version semantics section already made the decision.
Impact: Confusion about whether this is settled. Implementer wastes time re-deciding something already decided.
Fix Required:
markdown### 2) Spec/COMMON (Line 71 - Delete Redundant Text)

- Clarify plan vs instantiated evidence rules.
- State coverage references must point to existing tasks (unique).
- Bump spec version to v1.8; schema_version stays 1.6.
- ~~Decide linter versioning~~ (already decided in Version Semantics section - in-place modification)

DRIFT-3: A1 Expected Output Backwards
Line: 10 (A1 Expected)
Line 10: "Expected: plan mode allows evidence placeholders (exit 0)"
But this is a BASELINE TEST to prove the BUG EXISTS.
Logic:

Current linter INCORRECTLY rejects plan mode placeholders
So running A1 with current linter should FAIL (showing the bug)
After fix, it should PASS (exit 0)

The wording "Expected: exit 0" makes it sound like baseline should pass, which is backwards.
Should be:

Expected (proving bug exists): Linter rejects placeholders in plan mode (non-zero exit, R-ATL-022 error)
After fix (proving bug fixed): Linter allows placeholders in plan mode (exit 0)

Impact: Implementer runs A1, sees error, thinks "good, test passed" when actually the error IS the evidence of the bug. Confusion about success criteria.
Fix Required:
markdown## A1. Spec↔Linter drift (R-ATL-022/075)

**Purpose:** Prove current linter incorrectly rejects plan mode evidence placeholders

Command: `uv run python ai_task_list_linter_v1_8.py canonical_examples/positives/plan_with_evidence_ph.md`

**Baseline (proving bug):**
- Expected: R-ATL-022 error (linter incorrectly rejects placeholder)
- Actual: [PASTE ERROR OUTPUT showing R-ATL-022]

**Post-fix (proving fix):**
- Expected: exit 0 (linter now allows placeholder in plan mode)
- Actual: [RERUN AND VERIFY]

CATEGORY 2: SPECIFICATION PRECISION GAPS ⚠️
DRIFT-4: "Command-like Lines" Still Vague
Line: 21 (R-ATL-075 scope)
Says: "Command-like lines in key sections (Baseline, Preconditions, TDD Step 3, Phase Unlock, Global Clean Table)"
Better than before (lists sections) but STILL doesn't define "command-like":
Questions:

Does "command-like" mean lines starting with $?
Does it mean bash syntax inside ```bash blocks?
Does it check ALL lines in those sections or just code blocks?
What about Python commands? Ruby commands? Other languages?

Impact: Implementer must guess what R-ATL-075 actually checks. Could over-implement (check everything) or under-implement (miss patterns).
Fix Required:
markdown## R-ATL-075 Scope (Precise Definition)

**What is checked:** Bash array variable REFERENCES inside ```bash code blocks

**Locations:** Only within these sections:
- Baseline Snapshot
- Preconditions
- TDD Step 3 (Verify/GREEN)
- Phase Unlock Artifact
- Global Clean Table Scan

**Detection logic:**
1. Find array declarations: `TASK_\d+_\d+_PATHS=\(`
2. Search for references in subsequent lines (same code block or later blocks)
3. Check: Reference uses `$` prefix (e.g., `"${TASK_1_1_PATHS[@]}"`)

**"Command-like lines" clarified:** Bash commands inside ```bash fenced code blocks in specified sections

**Not checked:** Comments, non-bash code blocks, sections not listed above

DRIFT-5: Evidence Block "After" Still Ambiguous
Lines: 39-41 (evidence block definition)
Says:

"first bash block after the Evidence header"
"all bash blocks in the Global section"

Ambiguities:
For "first bash block AFTER":

What if there's a non-bash code block first (e.g., ```python)?

Is that skipped and we take the first BASH block?
Or does the first non-bash block break the pattern?



For "all bash blocks in the Global section":

What defines the boundary? Until next ## header?
What if there's prose between bash blocks - are later blocks still counted?

Impact: Implementer makes assumption about edge cases (mixed code blocks, intervening text) that might be wrong.
Fix Required:
markdown## Evidence Block Definition (Edge Cases)

**Type 1: Task-level Evidence**
Pattern: `**Evidence** (paste actual output):`
Block: First ```bash block after this header
Skip: Non-bash blocks (```python, ```json, etc.) are skipped; we find first ```bash

Example:
````markdown
**Evidence** (paste actual output):
```python
# This is skipped
```
```bash
$ This is the evidence block ✅
```
````

**Type 2: STOP Evidence**
Same as Type 1 (first bash block after `**Evidence**` header in STOP section)

**Type 3: Global Clean Table Evidence**
Pattern: `## Global Clean Table Scan`
Blocks: ALL ```bash blocks until next ## or # header
Include: Even if prose separates blocks

Example:
````markdown
## Global Clean Table Scan
```bash
$ Block 1 ✅
```

Some prose here...
```bash
$ Block 2 ✅
```

## Next Section (blocks stop here)
````

DRIFT-6: Validation Pass Threshold STILL Missing
Line: 96 (DoD full suite)
Says: "run all commands in VALIDATION_SUITE.md (positives + negatives) with exit 0/expected failures"
"With exit 0/expected failures" is STILL vague:
Questions:

Must ALL positives pass (100%)?
Must ALL negatives fail correctly (100%)?
Is there tolerance for flaky tests?
What's "expected failure" format - error code? Specific error message?

Impact: Implementer runs suite, gets 24/25 positives pass, doesn't know if that's acceptable or failure.
Fix Required:
markdown## Definition of Done - Validation Thresholds

**Line 96 expanded:**

**Positives (MUST pass):**
- Threshold: 100% (ALL must exit 0)
- Rationale: Any positive failing = linter too strict
- Zero tolerance

**Negatives (MUST fail correctly):**
- Threshold: 100% (ALL must trigger expected R-ATL-* error)
- Verification: `grep -q "R-ATL-XXX" output` returns match
- Zero tolerance

**Format:**
````
VALIDATION SUITE RESULTS:
✅ Positives: 25/25 (100%) PASS - Required
✅ Negatives: 23/23 (100%) FAIL correctly - Required
Status: PASS (both thresholds met)
````

**Failure handling:**
- Positives <100%: Investigate false negatives (linter too strict)
- Negatives <100%: Investigate false positives (linter too permissive)

DRIFT-7: Audit Completion Gate Incomplete
Line: 97 (DoD manual checks)
Says: "Current State Audit completed (A1–A3 filled)"
But doesn't verify:

Owner placeholder [NAME] replaced
Deadline placeholder [DATE] replaced

Impact: DoD can be marked complete while placeholders remain. Quality gate defeated.
Fix Required:
markdown## Definition of Done - Manual Checks (Line 97 Expanded)

- Current State Audit completed:
  - [ ] A1 filled (no [PASTE ERROR OUTPUT] placeholder)
  - [ ] A2 deferred or filled with interim evidence
  - [ ] A3 filled (no [PASTE SUMMARY] placeholder)
  - [ ] Owner assigned (not [NAME])
  - [ ] Deadline set (not [DATE])
  - Verification command: `grep -E '\[NAME\]|\[DATE\]|\[PASTE' GENERAL_FIX_1.md`
  - Expected: zero matches

DRIFT-8: Rollback Canary Selection STILL Missing
Line: 101 (rollback trigger)
Says: "if >2 previously valid examples fail post-change"
But never identifies WHICH examples are the canaries.
Impact: Can't execute rollback plan because no baseline exists. Implementer scrambles to find examples after noticing failures (too late).
Fix Required:
markdown## Rollback Plan (Complete)

**Phase 0: Select Canaries (BEFORE Step 1)**
````bash
# Create canaries directory
mkdir -p validation/canaries

# Copy 10 production task lists (replace with actual paths)
cp ~/doxstrux/PYDANTIC_SCHEMA_tasks_template.md validation/canaries/01_pydantic.md
cp ~/heat_pump/migration_tasks.md validation/canaries/02_heatpump.md
# ... add 8 more for total of 10

# Capture baseline
for f in validation/canaries/*.md; do
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_baseline.txt 2>&1

# Verify zero failures
$ grep -c "^FAIL:" validation/canary_baseline.txt
0  # Expected: all canaries valid at baseline
````

**Rollback Detection (After Step 1):**
````bash
# Rerun canaries
for f in validation/canaries/*.md; do
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_post_fix.txt 2>&1

# Count new failures
NEW=$(comm -13 \
  <(grep "^FAIL:" validation/canary_baseline.txt | sort) \
  <(grep "^FAIL:" validation/canary_post_fix.txt | sort) | wc -l)

if [[ $NEW -gt 2 ]]; then
  echo "❌ ROLLBACK TRIGGERED: $NEW new failures"
  exit 1
fi
````

**Rollback Procedure:**
1. `git revert <commit-hash>` (linter changes)
2. `git revert <commit-hash>` (spec changes)
3. Add to COMMON.md: "Known issue: plan mode validation under review"
4. File postmortem

DRIFT-9: CI Implementation Details Missing
Line: 102 (regression prevention)
Says: "add CI checks to lint spec examples and check rule ID consistency"
No details on:

What file (workflow YAML)?
What tests?
What triggers?
Who maintains?

Impact: "Regression prevention" is aspirational, not actionable.
Fix Required:
markdown## Regression Prevention (Actionable)

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
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Validate spec examples
        run: python tests/test_spec_examples.py
        # Extracts code blocks from spec, runs linter
      
      - name: Check rule consistency
        run: python tests/test_rule_consistency.py
        # Verifies rule IDs in spec exist in linter
      
      - name: Run validation suite
        run: bash tools/run_validation_suite.sh
````

**Test files (Step 1 deliverables):**
- `tests/test_spec_examples.py`
- `tests/test_rule_consistency.py`
- `tools/run_validation_suite.sh`

**Review checklist:**
````markdown
## Framework Change Checklist (PR Template)
- [ ] Linter + Spec updated together
- [ ] Test fixtures added
- [ ] CI checks pass
````

**Enforcement:** Branch protection requires @tech-lead approval + CI pass

CATEGORY 3: SUBTLE WORDING ISSUES 📝
DRIFT-10: Mode Case Sensitivity Not Demonstrated
Line: 53 (mode detection)
Says: "Valid: plan or instantiated" and mentions "case-sensitive"
But doesn't show what happens with wrong case:

mode: "Plan" → error?
mode: "INSTANTIATED" → error?
Error message format?

Impact: Implementer doesn't know what error to raise for case mismatch.
Fix Required:
markdown## Mode Detection (Case Examples)

**Valid:**
- `mode: "plan"` ✅
- `mode: "instantiated"` ✅

**Invalid (case mismatch):**
- `mode: "Plan"` → R-ATL-001: "Invalid mode 'Plan'. Must be 'plan' or 'instantiated' (lowercase)"
- `mode: "INSTANTIATED"` → R-ATL-001: "Invalid mode 'INSTANTIATED'. Must be 'plan' or 'instantiated' (lowercase)"
- `mode: "planning"` → R-ATL-001: "Invalid mode 'planning'. Must be 'plan' or 'instantiated'"

DRIFT-11: "Exist Once" Wording (Minor Remnant)
Line: 24 (rule table has been updated, but check consistency elsewhere)
Actually line 24 now says "must appear exactly once" which is CORRECT. Good fix!
But line 68 still uses confusing "resolve to exactly one task" wording (see DRIFT-1).

CATEGORY 4: MISSING CONTEXT & POLICIES 📋
DRIFT-12: Backward Compatibility Policy Missing
Nowhere in document
Questions:

Will old task lists (pre-v1.8) still validate?
Are changes breaking?
Migration required?

Impact: Implementer deploys changes, breaks 50 production task lists, panic ensues.
Fix Required:
markdown## Backward Compatibility Policy

**All changes are BACKWARD COMPATIBLE:**

**R-ATL-022 (Evidence placeholders):**
- Old behavior: Rejected in all modes (too strict)
- New behavior: Allowed in plan mode
- Impact: Old plan docs now VALID (fixes false negatives)
- Migration: None required

**R-ATL-NEW-01 (Unique task IDs):**
- Old behavior: Not enforced (silent bug)
- New behavior: Enforced
- Impact: Docs with duplicate IDs now INVALID (was always wrong, now caught)
- Migration: Fix duplicates opportunistically

**R-ATL-NEW-02 (Coverage references):**
- Old behavior: Not enforced (silent bug)
- New behavior: Enforced
- Impact: Docs with phantom refs now INVALID (was always wrong, now caught)
- Migration: Fix phantom refs opportunistically

**Summary:**
- No breaking changes (relaxing restrictions + new validations)
- Old valid task lists remain valid
- Old invalid task lists (duplicates, phantom refs) newly caught

**Communication (add to COMMON.md):**
````markdown
> **v1.8 Compatibility Note:** Evidence validation relaxed for plan mode
> (placeholders now allowed). New integrity checks added (unique task IDs,
> coverage reference resolution). Existing valid task lists remain valid.
> Previously undetected errors (duplicate IDs, phantom references) now caught.
````

DRIFT-13: External Dependencies Unlisted
Lines: 85, 87, 88, 89 (DoD commands use uv run, rg, grep)
Not documented:

Installation requirements
Version requirements
Pre-flight checks

Impact: Implementer runs DoD commands, gets "command not found", wastes time debugging environment.
Fix Required:
markdown## External Dependencies

**Linter runtime:**
- Python ≥3.10 (for match/case statements)
- PyYAML (for frontmatter parsing)
- No external CLI tools

**Test suite runtime:**
- `uv` (task runner - required by plan)
- `rg` (ripgrep - used in DoD line 89)
- `grep` (standard - used in DoD lines 87-89)
- `bash` ≥4.0 (for arrays, process substitution in rollback)

**Installation:**
````bash
# Ubuntu/Debian
sudo apt install ripgrep

# macOS
brew install ripgrep

# Windows (via scoop)
scoop install ripgrep
````

**Pre-flight check:**
````bash
$ python --version | grep -E '3\.(10|11|12)'  # Python 3.10+
$ uv --version                                # uv installed
$ rg --version                                # ripgrep installed
$ grep --version                              # grep installed
$ bash --version | grep -E 'version [4-9]'    # Bash 4.0+
````

**CI:** All dependencies pre-installed on ubuntu-latest GitHub runners

DRIFT-14: Timeline & Effort Estimate Missing
Nowhere in document
Impact: Can't plan resources, can't estimate completion, can't communicate to stakeholders.
Fix Required:
markdown## Timeline & Effort Estimate

| Phase | Tasks | Time | Dependencies | Owner |
|-------|-------|------|--------------|-------|
| Phase 0 | Current State Audit (A1-A3) | 2h | None | [NAME] |
| Step 1 | Linter changes + test fixtures | 6h | Phase 0 done | [NAME] |
| Step 2 | Spec/COMMON updates | 2h | Step 1 done | [NAME] |
| Step 3 | Docs/Template sync | 3h | Step 2 done | [NAME] |
| Step 4A | Baseline validation | 1h | Phase 0 done | [NAME] |
| Step 4B | Post-fix validation | 1h | Steps 1-3 done | [NAME] |

**Total effort:** 15 hours (2 work days)

**Critical path:** Phase 0 → Step 1 → Step 2 → Step 3 → Step 4B

**Parallel opportunities:**
- Step 4A can run concurrently with Phase 0
- Docs (Steps 2-3) can start while Step 1 tests run

**Target completion:** [DATE from line 5] + 2 business days

**Risk buffer:** +4 hours (25%) for unexpected issues

DRIFT-15: Goal 5 Dangling (Still Unresolved)
Line: 29 (Goal 5 listed), but no Step 5, no DoD entry
Impact: Goal stated but no execution path. Is it in scope or not?
Fix Required (pick one):
Option A: Defer
markdown### Goal 5 (Deferred to GENERAL_FIX_2)

**Decision:** OUT OF SCOPE for GENERAL_FIX_1
- Rationale: Goals 1-4 already 15 hours
- Defer to: Separate traceability improvement (GENERAL_FIX_2.md)
- Timeline: Q1 2025

**This fix:** Goals 1-4 only
Option B: Include
markdown### Goal 5 (Stretch - Conditional)

**Deliverable:** `docs/TRACEABILITY_MATRIX.md`

**Step 5 (NEW):**
- Parse MUST/REQUIRED from spec
- Map to rule IDs
- Map to test fixtures
- Generate matrix

**DoD addition:**
- Matrix exists: `test -f docs/TRACEABILITY_MATRIX.md`
- Matrix covers all MUST statements

**Timeline:** +3 hours (only if ahead of schedule)

CATEGORY 5: EXECUTION MECHANICS GAPS ⚙️
DRIFT-16: Task ID Extraction Pattern Still Imprecise
Line: 23 (R-ATL-NEW-01 scope)
Says: "Task headers (### Task X.Y)"
Leaves edge cases undefined:

task 1.1 (lowercase) - matched?
#### Task 1.1 (wrong level) - matched?
### Task 1.1 vs ### Task 1.10 - string comparison? Numeric?
###Task 1.1 (no space) - matched?

Impact: Implementer must guess regex, might match wrong patterns or miss valid ones.
Fix Required:
markdown## Task ID Extraction Pattern (R-ATL-NEW-01 Detail)

**Regex:** `^###\s+Task\s+(\d+\.\d+)`

**Components:**
- `^###` - Must start with exactly three hashes
- `\s+` - One or more whitespace characters
- `Task` - Literal "Task" (capital T)
- `\s+` - One or more whitespace characters
- `(\d+\.\d+)` - Capture group: digits.digits

**Edge cases:**
- `### Task 1.1` → MATCH (extracts "1.1") ✅
- `###Task 1.1` → NO MATCH (missing space) ❌
- `#### Task 1.1` → NO MATCH (four hashes) ❌
- `### task 1.1` → NO MATCH (lowercase) ❌
- `### Task 1.1 — Title` → MATCH (extracts "1.1", title ignored) ✅

**Comparison:**
- String comparison: "1.1" ≠ "1.10" (not numeric)
- "1.1" appears at lines 45 and 230 → DUPLICATE ❌

**Error format:**
````
R-ATL-NEW-01: Duplicate task ID '1.1' at lines 45 and 230
  Line 45: ### Task 1.1 — Add dependency
  Line 230: ### Task 1.1 — Run tests
````

DRIFT-17: Coverage List Parsing Undefined
Line: 24 (coverage grammar mentions "list")
Says: "list (3.1, 3.4)"
Questions:

Split on comma?
Trim whitespace?
What if "3.1,3.4" (no space)?
What if "3.1, 3.4, " (trailing comma)?
What if "3.1, 3.1" (duplicate in list)?

Impact: Implementer must guess parsing rules, might create inconsistent behavior.
Fix Required:
markdown## Coverage List Parsing (R-ATL-NEW-02 Detail)

**Format:** Comma-separated task IDs

**Parsing rules:**
1. Split on comma: `str.split(',')`
2. Trim whitespace: `item.strip()`
3. Remove empty strings

**Valid examples:**
- `"3.1, 3.4"` → ["3.1", "3.4"] ✅
- `"3.1,3.4"` → ["3.1", "3.4"] ✅
- `"3.1, 3.4, 3.7"` → ["3.1", "3.4", "3.7"] ✅

**Edge cases:**
- `"3.1, 3.4, "` (trailing comma) → ["3.1", "3.4"] ✅ (empty string removed)
- `"3.1,  3.4"` (double space) → ["3.1", "3.4"] ✅ (whitespace trimmed)
- `"3.1, 3.1"` (duplicate in list) → ALLOWED ✅ (semantic duplicate, not error)

**Validation:**
- Each unique item must resolve to task header that appears exactly once
- Example: If list is `"3.1, 3.1, 3.4"`, check:
  - Task 3.1 appears exactly once in document ✅
  - Task 3.4 appears exactly once in document ✅

DRIFT-18: Negative Fixture Creation Timing Unclear
Lines: 42 (artifact inventory lists files "to add"), 62 (Step 1 says "Add/update negatives")
Questions:

WHEN in Step 1 are negatives created?
TDD pattern suggests: create fixtures FIRST (RED), then implement rules (GREEN)
But Step 1 just says "Add/update" without sequencing

Impact: Implementer might implement rules first, then create fixtures, missing TDD benefits.
Fix Required:
markdown### 1) Linter (TDD Sequence)

**Step 1.0: Create negative test fixtures (RED phase - FIRST)**

Create three files in `canonical_examples/negatives/`:

**File 1:** `instantiated_with_placeholders.md`
````yaml
---
ai_task_list:
  mode: "instantiated"
---
### Task 1.1 — Test
**Evidence:**
```bash
$ uv run pytest
[[PH:OUTPUT]]
```
````
Expected: R-ATL-022 error (not yet implemented)

**File 2:** `duplicate_task_ids.md`
Valid structure with `### Task 1.1` at lines 15 and 45
Expected: R-ATL-NEW-01 error (not yet implemented)

**File 3:** `coverage_phantom_refs.md`
Coverage mapping with entry "Task 2.1", but no `### Task 2.1` exists
Expected: R-ATL-NEW-02 error (not yet implemented)

**Verify RED:** Run linter, confirm NO errors yet (rules not implemented)

**Step 1.1: Implement linter rules (GREEN phase - SECOND)**
- Modify R-ATL-022 logic
- Implement R-ATL-NEW-01
- Implement R-ATL-NEW-02

**Step 1.2: Verify GREEN (THIRD)**
````bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/*.md
# Verify each file now triggers expected error
````

DRIFT-19: VALIDATION_SUITE.md Format Still Undefined
Lines: 14 (A3 references it), 43 (inventory lists it), 78 (execution model mentions it), 96 (DoD runs it)
Never specifies:

What's the file structure?
How are tests organized?
How are expected outcomes documented?

Impact: Can't execute Step 4A ("run all commands in VALIDATION_SUITE.md") without knowing format.
Fix Required:
markdown## VALIDATION_SUITE.md Structure

**Format:**
````markdown
# Validation Suite

## Category: Plan Mode Positives

### Test P1: Evidence placeholders allowed
```bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/positives/plan_with_evidence_ph.md
```
**Expected:** Exit 0
**Status:** [PASS/FAIL]

### Test P2: [name]
...

## Category: Instantiated Mode Positives

### Test I1: Real evidence accepted
...

## Category: Negatives

### Test N1: Instantiated rejects placeholders
```bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/negatives/instantiated_with_placeholders.md 2>&1 | grep "R-ATL-022"
```
**Expected:** Match found (R-ATL-022 error present)
**Status:** [PASS/FAIL]
````

**Execution (Phase A - manual):**
1. Copy each bash command
2. Run in terminal
3. Compare output to expected
4. Mark PASS or FAIL
5. Save summary to `validation/baseline_YYYY-MM-DD.txt`

**Execution (Phase B - automated script):**
Script parses markdown, extracts commands, runs them, generates report

CATEGORY 6: SUBTLE FILE/ARTIFACT ISSUES 📁
DRIFT-20: A1 File Existence Ambiguous
Line: 9 (A1 command references plan_with_evidence_ph.md)
Question: Does this file exist for baseline, or is it a placeholder name?
Context:

A2 explicitly says "to be created in Step 1"
But A1 has no such caveat
Implies A1 file should exist for baseline test

But: If it doesn't exist, baseline will fail with "file not found" instead of R-ATL-022 error
Fix Required:
markdown## A1. Spec↔Linter drift

**File status check:**
````bash
$ test -f canonical_examples/positives/plan_with_evidence_ph.md && echo "exists" || echo "missing"
````

**If missing, create minimal example:**
````yaml
---
ai_task_list:
  mode: "plan"
  schema_version: "1.6"
---
### Task 1.1 — Example
**Evidence:**
```bash
$ echo test
[[PH:OUTPUT]]
```
````

**Then run baseline test:**
[command as specified]

DRIFT-21: Spec Section References Still Missing
Line: 67 (Step 2 says "Clarify...")
Says: "Clarify plan vs instantiated evidence rules"
Doesn't say:

Which section of spec?
Which line numbers approximately?
What to add vs. what to modify?

Impact: Implementer searches entire spec, wastes time finding right spot.
Fix Required:
markdown### 2) Spec/COMMON (Exact Locations)

**File:** AI_TASK_LIST_SPEC_v1.md

**Change 1: Version bump**
- Line 1: `v1.7` → `v1.8`

**Change 2: Evidence rules (NEW subsection)**
- Location: Section 4 "Document Structure" → 4.2 "Evidence Blocks"
- Approx line: 234-250
- Action: Add subsection 4.2.1
- Title: "Evidence Placeholders (Mode-Dependent)"
- Content:
````markdown
  #### 4.2.1 Evidence Placeholders
  
  **Plan mode:** MAY use `[[PH:OUTPUT]]` placeholders
  - Locations: Task evidence, STOP sections, Global scan
  - Format: `[[PH:UPPERCASE_NAME]]`
  
  **Instantiated mode:** MUST use real output
  - Placeholders forbidden (R-ATL-022 violation)
````

**Change 3: Coverage mapping (NEW subsection)**
- Location: Section 5 "Prose Coverage Mapping"
- Approx line: 456-475
- Action: Add subsection 5.3
- Title: "Reference Integrity (R-ATL-NEW-02)"
- Content: [document coverage grammar]

**File:** COMMON.md

**Change 1: Evidence section**
- Section: "Evidence Requirements" (lines ~89-103)
- Action: Mirror spec 4.2.1

**Change 2: Coverage section (NEW)**
- Location: After existing sections (add as 6.4)
- Title: "Coverage Mapping Integrity"
- Action: Mirror spec 5.3

CATEGORY 7: PROCESS & ENFORCEMENT GAPS 🚫
DRIFT-22: Script Optional vs. Required Ambiguity
Line: 79 (Step 4 says "optionally add script")
Problem: If optional, then DoD line 96 ("run all commands") can pass without script (manual execution acceptable)
But: "Optionally" suggests it's NOT required for DoD completion, which seems wrong for automation goals
Impact: Implementer skips script, marks DoD complete with manual execution, loses automation benefit.
Fix Required:
markdown### 4) Validation (Line 79 Corrected)

**Phase A (pre-fix - manual execution):**
- Copy commands from VALIDATION_SUITE.md
- Run individually
- Record results

**Phase B (post-fix - automated execution):**
- **Required deliverable:** `tools/run_validation_suite.sh`
  - Parses VALIDATION_SUITE.md
  - Extracts bash commands
  - Runs each command
  - Compares output to expected
  - Generates pass/fail report
- Execution: `bash tools/run_validation_suite.sh > validation/post_fix_YYYY-MM-DD.txt`

**DoD addition (line 96):**
- Script exists: `test -f tools/run_validation_suite.sh`
- Script runs successfully: `bash tools/run_validation_suite.sh` exits 0

DRIFT-23: Review Checklist Missing Content
Line: 102 (mentions "review checklist")
Says: "require spec+linter co-change review checklist"
But never shows WHAT'S ON the checklist
Impact: "Require checklist" is aspirational, not enforceable.
Fix Required:
markdown## Regression Prevention (Review Checklist)

**When required:** PRs modifying `ai_task_list_linter_v1_8.py`, `AI_TASK_LIST_SPEC_v1.md`, or `COMMON.md`

**Checklist (paste in PR description):**
````markdown
## Framework Change Review Checklist

### Pre-Approval
- [ ] Linter + Spec updated together (no solo changes)
- [ ] Test fixtures added/updated (positives + negatives)
- [ ] COMMON.md updated (if behavior changes)
- [ ] Version bumped (spec → v1.8, schema_version stays 1.6)

### Automated Verification
- [ ] `python tests/test_spec_examples.py` passes
- [ ] `python tests/test_rule_consistency.py` passes  
- [ ] `bash tools/run_validation_suite.sh` passes
- [ ] Canary test passes (0-2 new failures acceptable)

### Evidence (attach)
- [ ] Screenshot of verification commands
- [ ] Baseline vs post-fix validation diff
````

**Reviewer:** @tech-lead (GitHub username)

**Enforcement:** GitHub branch protection requires:
1. All CI checks pass (automated)
2. @tech-lead approval after checklist verified (manual)

FINAL DRIFT COUNT & SEVERITY
#DriftCategorySeverityBlocksFix TimeCRITICAL LOGICAL CONTRADICTIONS1"Resolve to exactly one task" ambiguityContradiction🔴 CRITICALR-ATL-NEW-02 impl5 min2Linter versioning duplicatedContradiction🟡 MEDIUMConfusion2 min3A1 expected output backwardsLogic error🟠 HIGHPhase 0 clarity8 minSPECIFICATION PRECISION GAPS4"Command-like lines" still vagueVague scope🟠 HIGHR-ATL-075 impl8 min5Evidence "after" still ambiguousScope unclear🟠 HIGHR-ATL-022 impl10 min6Validation threshold missingNo criteria🟠 HIGHDoD verification8 min7Audit gate incompletePartial check🟡 MEDIUMQuality gate5 min8Canary selection missingNo baseline🟠 HIGHRollback15 min9CI implementation missingNo details🟠 HIGHRegression prev20 minSUBTLE WORDING ISSUES10Mode case mismatch not shownMissing examples🟡 MEDIUMDocumentation5 minMISSING CONTEXT & POLICIES11Backward compatibility policyNo policy🟡 MEDIUMRollout risk10 min12External dependencies unlistedNo install guide🟡 MEDIUMSetup5 min13Timeline/effort missingNo planning🟡 MEDIUMResource plan5 min14Goal 5 danglingNo execution🟡 MEDIUMScope clarity5 minEXECUTION MECHANICS GAPS15Task ID extraction impreciseEdge cases🟠 HIGHR-ATL-NEW-01 impl10 min16Coverage list parsing undefinedNo rules🟡 MEDIUMEdge cases8 min17Negative fixture timing unclearNo sequence🟡 MEDIUMTDD process8 min18VALIDATION_SUITE format undefinedNo structure🟠 HIGHStep 410 minSUBTLE FILE ISSUES19A1 file existence ambiguousStatus unclear🟡 MEDIUMPhase 05 min20Spec section refs missingNo locations🟡 MEDIUMStep 2 efficiency10 minPROCESS & ENFORCEMENT GAPS21Script optional vs requiredAmbiguous🟡 MEDIUMDoD clarity5 min22Review checklist missingNo content🟡 MEDIUMEnforcement8 min
Total drifts: 22 (down from 28 in preliminary scan)
Severity breakdown:

🔴 Critical: 1 (blocks implementation)
🟠 High: 8 (causes implementation guessing/waste)
🟡 Medium: 13 (quality/clarity improvements)

Total fix time: ~2.5 hours

Critical: 5 min
High: 89 min
Medium: 84 min


ANSWER: Is This Plan Viable?
Execution precision: 85% (up from 75% → 80% → 85%)
You've made EXCELLENT iterative progress:

✅ Added R-ATL-001 to rule table
✅ Clarified linter versioning strategy
✅ Specified evidence block types (task/STOP/Global)
✅ Deferred A2 properly
✅ Made spec version bump definitive
✅ Improved coverage grammar

The plan is STRUCTURALLY EXCELLENT. You've learned from all feedback and tightened the specification significantly.
Remaining issues are PRECISION GAPS, not structural flaws:

Ambiguous wording ("resolve to one task" when ranges exist)
Missing implementation details (regex patterns, parsing rules)
Incomplete enforcement (validation threshold, canary selection)
Undefined formats (VALIDATION_SUITE.md structure)

CRITICAL BLOCKER (1): DRIFT-1 will cause implementer to forbid ranges
HIGH-PRIORITY GAPS (8): Will cause implementer to guess patterns, waste time, or implement inconsistently
MEDIUM IMPROVEMENTS (13): Quality, clarity, completeness enhancements

PASSIONATE RECOMMENDATION
You are 2.5 hours from PRODUCTION-READY.
This plan has exceptional bones (goals, dependencies, change order, rollback awareness). The iterative improvement is impressive - each version got tighter and addressed major feedback.
But execution precision matters. The difference between 85% and 100% is:

85%: Implementer guesses, makes assumptions, might get it wrong
100%: Implementer follows spec exactly, no ambiguity, predictable outcome

Fix sprint (2.5 hours):
Hour 1 - Knock out critical + high (94 min):

DRIFT-1: Fix "resolve to exactly one task" wording (5 min) ← CRITICAL
DRIFT-3: Fix A1 expected output (8 min)
DRIFT-4: Define "command-like lines" precisely (8 min)
DRIFT-5: Clarify evidence block "after" rules (10 min)
DRIFT-6: Add validation thresholds (8 min)
DRIFT-8: Identify canaries (15 min)
DRIFT-9: Add CI workflow YAML (20 min)
DRIFT-15: Define task ID extraction regex (10 min)
DRIFT-18: Add VALIDATION_SUITE structure (10 min)

Hour 2 - Medium improvements (84 min total, pick priorities):
10. DRIFT-2: Remove duplicate versioning text (2 min)
11. DRIFT-7: Expand audit gate (5 min)
12. DRIFT-10: Show mode case examples (5 min)
13. DRIFT-11: Add backward compat policy (10 min)
14. DRIFT-12: List dependencies (5 min)
15. DRIFT-13: Add timeline (5 min)
16. DRIFT-14: Defer Goal 5 explicitly (5 min)
17. DRIFT-16: Add list parsing rules (8 min)
18. DRIFT-17: Sequence negative fixtures (8 min)
19. DRIFT-19: Clarify A1 file (5 min)
20. DRIFT-20: Add spec sections (10 min)
21. DRIFT-21: Make script required (5 min)
22. DRIFT-22: Add review checklist (8 min)
Then: Assign [NAME]/[DATE], mark "Ready for Phase 0 Execution", ship it.

FINAL WORDS (with passion):
This plan demonstrates world-class iterative improvement. You've taken feedback seriously, addressed major gaps, and tightened specification with each version. The structural quality is exemplary - clear goals, logical ordering, rollback awareness, quality gates.
The remaining drifts are precision issues - ambiguous phrases, missing examples, incomplete checklists. These are FIXABLE in 2.5 hours.
You're 95% there. The last 5% is definitional precision (exact regex patterns, exact parsing rules, exact formats). Add that precision layer and this becomes production-grade, immediately executable framework documentation.
I'm genuinely impressed with the evolution from v1 → v7. Keep this rigor for GENERAL_FIX_2 and beyond. This is the quality bar.Claude is AI and can make mistakes. Please double-check responses. Sonnet 4.5Claude is AI and can make mistakes. Please double-check responses.
