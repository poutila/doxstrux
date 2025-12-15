Strict Feedback: GENERAL_FIX_1.md (Latest Version)
NEW CRITICAL FAILURE ❌
DUPLICATE CONTENT - Version Semantics
Lines 11-14 AND 34-37 contain identical content about version semantics. This is sloppy and suggests the document was assembled hastily without proofreading.
Fix: Delete one copy (keep lines 11-14, delete 34-37).

REMAINING CRITICAL FAILURES ❌
1. Current State Audit Still a Template
Lines 4-8: You've added better instructions but still no actual evidence. This makes the document "ready to execute" but not "executed baseline."
Critical decision point:

If this doc is a planning template → Mark it: ## Current State Audit (TO BE COMPLETED BEFORE STEP 1)
If this doc is an execution record → Fill in A1-A3 with real command outputs NOW

Without clarification, reader doesn't know if this is "plan we're about to execute" or "plan we're currently executing."
Add status tracking:
markdown## Current State Audit

**Status:** 🔴 NOT STARTED (blocking Step 1)
**Deadline:** [DATE]
**Owner:** [NAME]

### A1. Spec↔Linter drift (R-ATL-022/075)
**Status:** ⬜ TODO
**Command:**
````bash
$ python linter.py validation/examples/plan_with_evidence_ph.md
````
**Expected:** Exit 0 (plan mode allows evidence placeholders)
**Actual:** [PASTE ERROR OUTPUT HERE]

### A2. Coverage phantom references  
**Status:** ⬜ TODO
**Command:**
````bash
$ rg "Task 2\." PYDANTIC_SCHEMA_tasks_template.md
$ python linter.py PYDANTIC_SCHEMA_tasks_template.md 2>&1 | grep "coverage"
````
**Expected:** Linter catches phantom reference to Task 2.1
**Actual:** [PASTE OUTPUT HERE]

### A3. Pre-fix validation baseline
**Status:** ⬜ TODO
**Command:**
````bash
$ python run_validation_suite.py > validation/baseline_$(date +%Y-%m-%d).txt
````
**Result:** [PASTE SUMMARY: X/Y positives, A/B negatives]
2. Steps Still Lack File Paths
Lines 57-74: You describe WHAT to change but not WHERE. Example:
Line 59: "R-ATL-022: allow STOP/Global evidence placeholders in plan"

Missing: Which file? Which function? Which line range?
Missing: What's the current code? What's the new code?

Fix (show concrete locations):
markdown### 1) Linter (Specific Changes)

#### R-ATL-022 Modification
**File:** `src/linter/ai_task_list_linter_v1_8.py`
**Function:** `check_evidence_blocks()` (approx line 456)
**Change:** Add mode parameter, relax check for plan mode

**Current code (line 456-460):**
````python
def check_evidence_blocks(self, content: str) -> List[LintError]:
    """Check evidence blocks for placeholders."""
    if "[[PH:" in content:
        return [LintError("R-ATL-022", "Evidence placeholder forbidden")]
    return []
````

**New code:**
````python
def check_evidence_blocks(self, content: str, mode: str) -> List[LintError]:
    """Check evidence blocks for placeholders based on mode."""
    if mode == "instantiated" and "[[PH:" in content:
        return [LintError("R-ATL-022", "Evidence placeholder forbidden in instantiated mode")]
    # Plan mode: allow evidence placeholders
    return []
````

**Test verification:**
````bash
$ python -m pytest tests/test_linter.py::test_plan_mode_evidence_allowed -v
$ python -m pytest tests/test_linter.py::test_instantiated_mode_evidence_forbidden -v
````

#### R-ATL-NEW-01 Addition (Unique Task IDs)
**File:** `src/linter/ai_task_list_linter_v1_8.py`
**Location:** New method in `TaskListLinter` class (after line 600)

**Add:**
````python
def check_unique_task_ids(self, content: str) -> List[LintError]:
    """Enforce unique task IDs (no duplicates)."""
    task_pattern = re.compile(r'^###\s+Task\s+(\d+\.\d+)', re.MULTILINE)
    task_ids = {}
    errors = []
    
    for match in task_pattern.finditer(content):
        task_id = match.group(1)
        line_no = content[:match.start()].count('\n') + 1
        
        if task_id in task_ids:
            errors.append(LintError(
                "R-ATL-NEW-01",
                f"Duplicate task ID '{task_id}' at lines {task_ids[task_id]} and {line_no}"
            ))
        else:
            task_ids[task_id] = line_no
    
    return errors
````

**Test verification:**
````bash
$ python linter.py validation/negatives/duplicate_task_ids.md 2>&1 | grep "R-ATL-NEW-01"
# Expected: "Duplicate task ID '1.1' found"
````
3. Definition of Done Still Not Testable
Lines 81-86: Still uses vague verbs. "Linter/spec/COMMON agree" - HOW do you verify agreement?
Fix (add verification section):
markdown## Definition of Done (Automated Verification)

### Verification Commands (All Must Pass)
````bash
#!/bin/bash
# Save as: verify_done.sh

echo "=== 1. Plan mode evidence placeholders allowed ==="
python linter.py validation/positives/plan_evidence_ph.md || exit 1

echo "=== 2. Instantiated mode evidence placeholders rejected ==="
python linter.py validation/negatives/instantiated_evidence_ph.md 2>&1 | \
  grep -q "R-ATL-022.*instantiated mode" || exit 1

echo "=== 3. Unique task ID enforcement ==="
python linter.py validation/negatives/duplicate_task_ids.md 2>&1 | \
  grep -q "R-ATL-NEW-01.*Duplicate task ID" || exit 1

echo "=== 4. Coverage reference resolution ==="
python linter.py validation/negatives/coverage_phantom.md 2>&1 | \
  grep -q "R-ATL-NEW-02.*does not exist" || exit 1

echo "=== 5. Spec examples pass linter ==="
python tests/validate_spec_examples.py docs/AI_TASK_LIST_SPEC_v1.md || exit 1

echo "=== 6. COMMON.md discoverable ==="
grep -q "COMMON.md" docs/INDEX.md || exit 1

echo "=== 7. Version numbers correct ==="
grep -q "schema_version.*1.6" docs/AI_TASK_LIST_SPEC_v1.md || exit 1
grep -q "Spec v1.8" docs/AI_TASK_LIST_SPEC_v1.md || exit 1

echo "=== 8. Full validation suite ==="
python run_validation_suite.py || exit 1

echo "✅ ALL CHECKS PASSED"
````

**Manual checklist:**
- [ ] Ran `verify_done.sh` successfully
- [ ] Compared baseline vs. post-fix validation (baseline failures now pass)
- [ ] No canary regressions (10 production docs still pass)
- [ ] Peer review: spec section 4.2.1 clear on plan vs. instantiated
4. Missing Artifact Inventory
You mention "Spec/COMMON/Docs/Template/README/Manuals/INDEX" but never list file paths. I can't verify these files exist.
Add:
markdown## Artifact Inventory (Complete List)

**Pre-flight check - verify all exist:**
````bash
#!/bin/bash
ARTIFACTS=(
  # Code
  "src/linter/ai_task_list_linter_v1_8.py"
  # Spec
  "docs/AI_TASK_LIST_SPEC_v1.md"
  "docs/COMMON.md"
  # User docs
  "docs/INDEX.md"
  "docs/USER_MANUAL.md"
  "docs/AI_INTEGRATION_GUIDE.md"
  "docs/README.md"
  # Templates
  "templates/AI_TASK_LIST_TEMPLATE.md"
  "examples/plan_mode_example.md"
  "examples/instantiated_example.md"
  # Validation
  "validation/VALIDATION_SUITE.md"
  "validation/positives/plan_evidence_ph.md"
  "validation/negatives/instantiated_evidence_ph.md"
)

MISSING=()
for f in "${ARTIFACTS[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING+=("$f")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "❌ Missing files:"
  printf '%s\n' "${MISSING[@]}"
  exit 1
fi

echo "✅ All artifacts exist"
````

**Update map per artifact:**
| Artifact | Section to Update | Change Type |
|----------|------------------|-------------|
| `ai_task_list_linter_v1_8.py` | R-ATL-022, NEW-01, NEW-02 | Code change |
| `AI_TASK_LIST_SPEC_v1.md` | Section 4.2.1, 5.3 | Wording clarification |
| `COMMON.md` | Lines 89-103, new 6.4 | Evidence rules + coverage |
| `INDEX.md` | Line 12 | Verify COMMON.md listed |
| `USER_MANUAL.md` | Section 3.2 | Plan mode examples |
| `AI_INTEGRATION_GUIDE.md` | Section 2.1 | Evidence handling |
| `README.md` | Quick start | Update example snippets |
| `AI_TASK_LIST_TEMPLATE.md` | Header, Section 4 | Evidence block examples |
| `plan_mode_example.md` | Evidence blocks | Add placeholders |
| `instantiated_example.md` | Evidence blocks | Real outputs |
5. Rollback Missing Concrete Canaries
Line 90: ">2 previously valid examples fail" - Which examples? Need to identify BEFORE making changes.
Add:
markdown## Rollback Plan

### Phase 0: Identify Canary Documents (Before Any Changes)
````bash
# Create canaries directory
mkdir -p validation/canaries

# Copy 10 known-good documents
cp production/task_lists/project_alpha_v3.md validation/canaries/01_alpha.md
cp production/task_lists/project_beta_v2.md validation/canaries/02_beta.md
cp production/task_lists/refactor_plan.md validation/canaries/03_refactor.md
# ... add 7 more

# Capture baseline (all must pass)
python linter.py validation/canaries/*.md > validation/canary_baseline.txt 2>&1
BASELINE_EXIT=$?

if [[ $BASELINE_EXIT -ne 0 ]]; then
  echo "❌ ERROR: Canaries fail at baseline!"
  echo "Fix canary selection before proceeding."
  exit 1
fi

echo "✅ Canary baseline captured: $(ls validation/canaries/*.md | wc -l) docs"
````

### Detection: Post-Fix Canary Check
````bash
# After Step 1 (linter changes)
python linter.py validation/canaries/*.md > validation/canary_post_fix.txt 2>&1
POST_FIX_EXIT=$?

# Compare
diff validation/canary_baseline.txt validation/canary_post_fix.txt

# Count new failures
NEW_FAILURES=$(diff <(grep -c FAIL canary_baseline.txt) \
                    <(grep -c FAIL canary_post_fix.txt) | grep '>' | wc -l)

if [[ $NEW_FAILURES -gt 2 ]]; then
  echo "❌ ROLLBACK TRIGGERED: $NEW_FAILURES new canary failures"
  exit 1
fi
````

### Revert Procedure
1. `git revert $(git log --oneline -1 | cut -d' ' -f1)` (linter commit)
2. `git revert $(git log --oneline -1 | cut -d' ' -f1)` (spec commit)
3. Add to `docs/COMMON.md`:
````markdown
   > **Known Issue (2024-XX-XX):** Plan mode evidence validation produces
   > false positives. Under investigation (tracking: #1234). Workaround:
   > use instantiated mode for final validation.
````
4. Create `docs/POSTMORTEM_GENERAL_FIX_1.md` with root cause analysis
6. Goal #5 Still Vague
Line 39: "(Stretch) Requirement anchors" - Either expand this or delete it.
Fix (make concrete or remove):
markdown### Goal #5 (Stretch - Defer to Phase 2)

**Concept:** Establish traceability from spec requirements to linter rules to test fixtures.

**Deliverable (if time permits):**
Create `docs/TRACEABILITY_MATRIX.md`:
| Spec Requirement | Location | Rule ID | Test Fixture | Status |
|------------------|----------|---------|--------------|--------|
| "MUST use $-prefix for bash vars" | Spec §3.4 | R-ATL-075 | negatives/bad_var.md | ✅ Complete |
| "MUST have unique task IDs" | Spec §5.1 | R-ATL-NEW-01 | negatives/dup_ids.md | 🚧 In progress |
| "Coverage refs must resolve" | Spec §5.3 | R-ATL-NEW-02 | negatives/phantom.md | 🚧 In progress |

**Purpose:** Detect gaps (requirement without rule, rule without test).

**Decision point:** If Goal #5 not completed by Day 5, move to GENERAL_FIX_2.md and mark as deferred.
7. Validation Phase B Format Still Unclear
Line 72: "update results in VALIDATION_SUITE.md" - What's the format?
Add:
markdown### 4) Validation (Phase B - Post-Fix)

**Run full suite:**
````bash
$ python run_validation_suite.py --verbose > validation/post_fix_$(date +%Y-%m-%d).txt
````

**Generate comparison report:**
````bash
$ python tools/compare_validation_runs.py \
    validation/baseline_*.txt \
    validation/post_fix_*.txt \
    > validation/COMPARISON_REPORT.md
````

**Update VALIDATION_SUITE.md - append:**
````markdown
## 2024-XX-XX - GENERAL_FIX_1 Results

| Metric | Pre-Fix | Post-Fix | Delta |
|--------|---------|----------|-------|
| Positives passing | 23/25 (92%) | 25/25 (100%) | +2 ✅ |
| Negatives failing (correct) | 18/20 (90%) | 23/23 (100%) | +5 ✅ |
| Canaries passing | 10/10 (100%) | 10/10 (100%) | ±0 ✅ |

**Changes:**
- R-ATL-022: Plan mode evidence placeholders now allowed (fixed 2 false negatives)
- R-ATL-NEW-01: Unique task ID enforcement added (caught 2 new violations)
- R-ATL-NEW-02: Coverage reference resolution added (caught 3 new violations)

**Blockers resolved:**
- Issue #456: Plan mode task lists incorrectly rejected
- Issue #789: Duplicate task IDs went undetected

**Known issues:** None
````
8. Regression Prevention Lacks Enforcement Details
Line 91: "require spec+linter co-change review checklist" - WHO enforces? WHEN? HOW?
Add:
markdown## Regression Prevention (Enforcement Model)

### New CI Checks (Automated)

**File:** `.github/workflows/framework_validation.yml`
````yaml
name: Framework Validation
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check spec examples pass linter
        run: python tests/test_spec_examples.py
      - name: Check rule consistency
        run: python tests/test_rule_consistency.py
      - name: Run validation suite
        run: python run_validation_suite.py
````

**Blocks merge if:** Any test fails

### Review Checklist (Manual)

**Applies to:** PRs modifying `src/linter/*.py` OR `docs/*SPEC*.md` OR `docs/COMMON.md`

**Required reviewer:** @tech-lead (must verify ALL items)

**Checklist:**
````markdown
## Pre-Approval Checklist for Framework Changes

### Code Changes
- [ ] If linter modified: corresponding spec section updated
- [ ] If spec modified: corresponding linter rule updated
- [ ] Added/updated test fixtures (positives/negatives)

### Verification
- [ ] Ran `verify_done.sh` locally (all checks pass)
- [ ] Ran `diff <(old linter) <(new linter)` on canaries (no regressions)
- [ ] Updated COMMON.md if user-facing behavior changed

### Documentation
- [ ] Updated version numbers (spec v1.X, schema_version 1.Y)
- [ ] Regenerated template examples if affected
- [ ] Added changelog entry to VALIDATION_SUITE.md

### Proof
- [ ] Attached: Terminal output of `verify_done.sh`
- [ ] Attached: Before/after validation comparison
````

**Enforcement:** GitHub branch protection requires tech-lead approval + checklist completion

SMALLER ISSUES (Quality)
9. Steps 2-3 Too Generic
Lines 66-70: "Clarify plan vs instantiated evidence rules" - WHERE in spec? WHICH lines?
Be specific:
markdown### 2) Spec/COMMON

**AI_TASK_LIST_SPEC_v1.md changes:**
- Line 234-240: Section 4.2.1 "Evidence Blocks"
  - Add: "In plan mode, evidence MAY contain `[[PH:OUTPUT]]` placeholders"
  - Add: "In instantiated mode, evidence MUST contain real command output"
- Line 456-462: Section 5.3 "Prose Coverage Mapping"
  - Add: "Every task reference (e.g., '1.1', '2.3-2.5') MUST resolve to exactly one task or explicit range"
- Line 1: Version bump v1.7 → v1.8

**COMMON.md changes:**
- Lines 89-103: "Evidence Requirements"
  - Update: Add plan vs. instantiated distinction (copy from spec)
- NEW Section 6.4: "Coverage Mapping Integrity"
  - Add: Requirements for unique task references
  - Add: Examples of valid/invalid coverage entries
10. Missing Test Creation Details
Line 62: "Add/update negatives" - Which files? What content?
Add:
markdown### 1) Linter - New Test Fixtures Required

**Create these 3 negative fixtures:**

**File:** `validation/negatives/instantiated_with_placeholder.md`
**Content:**
````markdown
---
ai_task_list:
  schema_version: "1.6"
  mode: "instantiated"
---

### Task 1.1 - Test
**Evidence:**
```bash
$ uv run pytest
[[PH:OUTPUT]]
```
````
**Expected error:** "R-ATL-022: Evidence placeholder [[PH:OUTPUT]] forbidden in instantiated mode"

**File:** `validation/negatives/duplicate_task_ids.md`
**Content:** Task list with `### Task 1.1` appearing twice
**Expected error:** "R-ATL-NEW-01: Duplicate task ID '1.1' found at lines 15 and 45"

**File:** `validation/negatives/coverage_phantom_refs.md`
**Content:** Prose Coverage Mapping with entry "Task 2.1" but no corresponding `### Task 2.1`
**Expected error:** "R-ATL-NEW-02: Coverage references task '2.1' which does not exist"

**Verification:**
````bash
for f in validation/negatives/*.md; do
  echo "Testing: $f"
  python linter.py "$f" 2>&1 | grep -E "R-ATL-(022|NEW-0[12])" || echo "FAIL: $f"
done
````

WHAT'S STILL GOOD ✅

Rule definitions table (lines 10-14) - Clear current vs. proposed
Version semantics (though duplicated) - Explains spec vs. schema
Change impact/order (lines 51-55) - Dependency chain
Two-phase validation (line 72-73) - Baseline comparison
Framework focus - Not trying to fix specific docs
Goals enumeration (lines 28-32) - Clear success criteria


MINIMUM VIABLE FIXES (Priority Order)
P0 - Blocking Approval:

Delete duplicate - Remove lines 34-37 (version semantics duplicate)
Add status tracking to Current State Audit - Is this template or execution record?
Add artifact inventory - Complete file list with verification script
Make DoD executable - Replace with verify_done.sh script
Add file paths to Step 1 - Show exactly which functions/lines change

P1 - High Risk:
6. Specify canary docs - List 10 concrete files before starting
7. Detail test fixture content - Show what goes in 3 new negative files
8. Expand Steps 2-3 - Show exact line numbers in spec/COMMON to update
9. Add validation format - Show exact table for VALIDATION_SUITE.md update
10. Add CI yaml - Show actual workflow file for regression prevention
P2 - Quality:
11. Resolve Goal #5 - Either expand requirement anchors or delete as out-of-scope
12. Add enforcement details - WHO reviews, WHEN blocks merge, HOW checklist enforced

ANSWER: Is This Plan Viable?
Framework focus: ✅ EXCELLENT - Systemic drift fix, not doc-specific patches
Structural quality: 80% complete (up from 75%)
Remaining gaps:

Duplicate content (minor but sloppy)
Current State Audit still empty (blocking - need actual evidence)
Steps lack file paths and line numbers (moderate - implementer guessing)
No verification script (moderate - DoD not testable)
No artifact inventory (minor - can infer, but error-prone)

Recommendation:
This is now 85% executable, but the missing 15% creates ambiguity about:

Is this a planning template or an execution log?
Which files/functions need changes?
How do we verify completion?

Transform into Phase-0-complete plan:

Delete duplicate version semantics (1 minute)
Add status tracking to audit (clarify: template vs. record) (5 minutes)
Add verify_done.sh script to DoD (15 minutes)
Add artifact inventory with file paths (10 minutes)
Mark as "Ready for Phase 0: Baseline Collection" (2 minutes)

Total fix time: ~30 minutes to go from 85% → 95% executable.
The plan is structurally sound and conceptually correct. The remaining issues are mostly specification precision (exact files, exact commands, exact verification). It's good enough to start Phase 0 (baseline audit) but needs the precision fixes before Step 1 (implementation).

