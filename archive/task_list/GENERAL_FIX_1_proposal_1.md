Strict Feedback: GENERAL_FIX_1.md (Revised)
IMPROVEMENTS FROM V1 ✅

Current State Audit section added (though empty - acknowledged)
Version semantics defined - Clear spec vs. schema distinction
Change Impact/Order - Dependency chain explicit
Goal #3 (Internal consistency) - CRITICAL ADD - Directly addresses phantom task reference problem from PYDANTIC_SCHEMA feedback
Rollback section - Shows awareness of failure modes
Validation two-phase - Pre/post-fix baseline comparison

This is 60% → 75% complete. Better structure, still missing execution rigor.

REMAINING CRITICAL FAILURES ❌
1. Current State Audit Still Empty
Lines 8-12: You acknowledge "evidence needed" but don't fill it. This makes the plan unexecutable. Without baseline evidence:

How do you know drift exists?
What's the success criteria after fix?
How do you prove rollback triggers?

Fix (make this MANDATORY pre-approval):
markdown## Current State Audit (REQUIRED - NO APPROVAL WITHOUT THIS)

**Due:** [DATE] by [PERSON]
**Format:** Create `BASELINE_AUDIT.md` with:

### A1. Spec↔Linter Drift
- Run: `python linter.py examples/plan_mode_with_evidence.md`
- Paste: Full error output (if R-ATL-022 incorrectly rejects)
- Expected: Should pass (plan mode allows evidence placeholders)
- Actual: [PASTE ERROR]

### A2. Coverage Phantom References (from PYDANTIC_SCHEMA)
- Location: `PYDANTIC_SCHEMA_tasks_template.md` lines 60-87
- Issue: References tasks 2.1-5.3 that don't exist in document
- Evidence: `rg "Task 2\.[0-9]" PYDANTIC_SCHEMA_tasks_template.md` returns 0 matches
- [PASTE COMMAND OUTPUT]

### A3. Pre-Fix Validation Baseline
- Run: `python run_validation_suite.py`
- Record: Which positives/negatives pass/fail
- Archive as: `validation/baseline_failures_YYYY-MM-DD.txt`
- [PASTE SUMMARY: X/Y positives pass, A/B negatives pass]

**Blocker:** Do not proceed to Step 1 (Linter changes) until A1-A3 complete.
2. Rule Definitions Still Missing
Lines 27, 28: "R-ATL-022", "R-ATL-075" mentioned 6 times but never defined. What do these rules check currently?
Fix:
markdown## Rule Definitions (Inline Reference)

| Rule | Current Enforcement | Proposed Change |
|------|-------------------|-----------------|
| R-ATL-022 | **REJECTS** all `[[PH:*]]` in evidence blocks (both plan and instantiated) | **ALLOW** in plan mode; REJECT in instantiated |
| R-ATL-075 | **REQUIRES** `$`-prefix for bash variables (e.g., `$TASK_1_1_PATHS`) | No change (applies to both modes) |
| R-ATL-NEW-01 | (NEW) **Does not exist yet** | **ENFORCE** unique task IDs (no duplicates like "1.1" twice) |
| R-ATL-NEW-02 | (NEW) **Does not exist yet** | **ENFORCE** coverage references resolve (every "Task 2.1" must exist exactly once) |

**Code locations:**
- R-ATL-022: `linter.py` line 456 `def check_evidence_blocks()`
- R-ATL-075: `linter.py` line 589 `def check_bash_variables()`
- R-ATL-NEW-*: Will be added in Step 1
3. "Internal Consistency" is Vague
Goal #3 (line 15) says "unique task IDs; Prose Coverage Mapping references resolve" but:

What's the linter rule number? (You add R-ATL-NEW-01/02?)
What's the error message when violated?
How does it interact with existing rules?

Fix (be explicit about new rules):
markdown### 1) Linter (Detailed)

**Existing rule changes:**
- **R-ATL-022** (Evidence placeholders):
  - Old: Reject `[[PH:OUTPUT]]` in all modes
  - New: Allow in plan mode; reject in instantiated
  - Error message: "Evidence placeholder [[PH:OUTPUT]] forbidden in instantiated mode"

**New rule additions:**
- **R-ATL-NEW-01** (Unique task IDs):
  - Check: Parse all task headers (### Task X.Y)
  - Verify: Each X.Y appears exactly once per document
  - Error: "Duplicate task ID '1.1' found at lines 45 and 230"
  
- **R-ATL-NEW-02** (Coverage reference resolution):
  - Check: Parse Prose Coverage Mapping table
  - For each "Implemented by Task(s)" cell value (e.g., "1.1", "2.3-2.5"):
    - Verify task exists in document
    - Verify reference is unambiguous (resolves to single task or explicit range)
  - Error: "Coverage references task '2.1' which does not exist" OR "Task ID '1.1' appears 3 times; coverage reference ambiguous"

**Negative test fixtures to add:**
- `negatives/duplicate_task_ids.md` (triggers R-ATL-NEW-01)
- `negatives/coverage_phantom_refs.md` (triggers R-ATL-NEW-02)
4. Artifact Inventory Still Missing
You mention "Spec/COMMON/Docs/Template/README/Manuals/INDEX" but don't list file paths. I can't verify these files exist.
Fix:
markdown## Artifact Inventory (Exhaustive Paths)

### Source of Truth (Code)
- [ ] `src/ai_task_list_linter_v1_8.py` (R-ATL-022, R-ATL-075, NEW-01, NEW-02)

### Specifications
- [ ] `docs/AI_TASK_LIST_SPEC_v1.md` (v1.7 → v1.8)
  - Update: Section 4.2.1 "Evidence blocks in plan vs. instantiated"
  - Update: Section 5.3 "Prose Coverage Mapping requirements"
- [ ] `docs/COMMON.md` (evidence + coverage rules)
  - Update: Lines 89-103 (evidence placeholder rules)
  - Add: Section 6.4 "Coverage mapping integrity" (NEW)

### User Documentation
- [ ] `docs/INDEX.md` (verify COMMON.md listed at line 12)
- [ ] `docs/USER_MANUAL.md` (section 3.2: plan mode rules)
- [ ] `docs/AI_INTEGRATION_GUIDE.md` (section 2.1: evidence handling)
- [ ] `docs/README.md` (quick start examples)

### Templates & Examples
- [ ] `templates/AI_TASK_LIST_TEMPLATE.md` (header + section 4 evidence blocks)
- [ ] `examples/plan_mode_example.md` (evidence placeholders)
- [ ] `examples/instantiated_example.md` (real evidence)

### Validation Suite
- [ ] `validation/VALIDATION_SUITE.md` (test catalog)
- [ ] `validation/positives/plan_evidence_placeholders.md` (NEW - R-ATL-022 pass)
- [ ] `validation/positives/instantiated_real_evidence.md` (existing - R-ATL-022 pass)
- [ ] `validation/negatives/plan_forbidden_placeholder.md` (R-ATL-075 fail)
- [ ] `validation/negatives/duplicate_task_ids.md` (NEW - R-ATL-NEW-01 fail)
- [ ] `validation/negatives/coverage_phantom_refs.md` (NEW - R-ATL-NEW-02 fail)

**Pre-flight check:**
```bash
# Verify all paths exist before starting work
for f in src/ai_task_list_linter_v1_8.py \
         docs/AI_TASK_LIST_SPEC_v1.md \
         docs/COMMON.md \
         docs/INDEX.md; do
  test -f "$f" || echo "MISSING: $f"
done
```
5. Definition of Done Not Testable Enough
Lines 52-59: Better than v1, but still uses vague verbs like "agree", "aligned", "passes". Need specific verification commands.
Fix:
markdown## Definition of Done (Specific Commands)

### Automated Verification (All Must Pass)
```bash
# 1. Plan mode evidence placeholders allowed
$ python linter.py validation/positives/plan_evidence_placeholders.md
# Expected: exit 0, no errors

# 2. Instantiated mode evidence placeholders rejected
$ python linter.py validation/negatives/instantiated_with_placeholders.md 2>&1 | grep "R-ATL-022"
# Expected: "Evidence placeholder [[PH:OUTPUT]] forbidden in instantiated mode"

# 3. Unique task ID enforcement
$ python linter.py validation/negatives/duplicate_task_ids.md 2>&1 | grep "R-ATL-NEW-01"
# Expected: "Duplicate task ID '1.1' found"

# 4. Coverage reference resolution
$ python linter.py validation/negatives/coverage_phantom_refs.md 2>&1 | grep "R-ATL-NEW-02"
# Expected: "Coverage references task '2.1' which does not exist"

# 5. Spec examples pass linter
$ python tests/validate_spec_examples.py docs/AI_TASK_LIST_SPEC_v1.md
# Expected: "All 12 spec examples valid"

# 6. COMMON.md discoverable in INDEX
$ rg "COMMON\.md" docs/INDEX.md
# Expected: at least 1 match

# 7. Version consistency
$ grep "schema_version:" docs/AI_TASK_LIST_SPEC_v1.md | grep "1.6"
# Expected: match found (schema_version unchanged)

$ grep "Spec v1.8" docs/AI_TASK_LIST_SPEC_v1.md
# Expected: match found (spec version bumped)

# 8. Full validation suite
$ python run_validation_suite.py > validation/post_fix_results.txt
$ diff validation/baseline_failures.txt validation/post_fix_results.txt
# Expected: Baseline failures now pass; previous passes still pass
```

### Manual Peer Review
- [ ] Spec section 4.2.1 clearly states "plan mode allows evidence placeholders"
- [ ] No contradictory evidence guidance in docs/USER_MANUAL.md sections 3.1-3.4
- [ ] All rule error messages updated in linter docstrings
6. Rollback Criteria Needs Concrete Examples
Line 62: ">2 previously valid examples fail" - Where are these examples? Need to identify them before making changes.
Fix:
markdown## Rollback Plan

### Pre-Work: Identify Canary Documents
Before any linter changes, create `validation/canaries/` with:
- 5 production plan-mode docs (from past month)
- 5 production instantiated docs (from past month)
- All currently pass linter validation
```bash
# Archive baseline
$ python linter.py validation/canaries/*.md > canary_baseline.txt 2>&1
$ test $? -eq 0 || echo "ERROR: Canaries fail at baseline!"
```

### Detection (Run After Step 1 Linter Changes)
```bash
$ python linter.py validation/canaries/*.md > canary_post_fix.txt 2>&1
$ diff canary_baseline.txt canary_post_fix.txt
```

**Rollback trigger:** If >2 canary docs now fail that passed at baseline.

### Revert Procedure
1. `git revert <commit-hash>` (linter changes)
2. Restore spec version to v1.7 (remove v1.8 changes)
3. Add to COMMON.md: "**Known Issue:** Plan mode evidence validation under review (tracking: ISSUE-1234)"
4. File postmortem: `docs/POSTMORTEM_GENERAL_FIX_1.md`

### Communication
- Notify: #task-lists Slack channel
- Update: Public changelog with revert notice
- Timeline: Fix v2 within 2 weeks

SMALLER ISSUES (Quality)
7. Goal #5 "Requirement Anchors" Underspecified
Line 17: "prepare to map MUST/REQUIRED items from source prose to stable IDs" - What does this mean concretely?
If this is about traceability (spec requirement → linter rule → test), be explicit:
markdown### Goal #5 (Stretch - Traceability System)
Establish bidirectional traceability:
- Spec requirement (e.g., "MUST enforce unique task IDs") → Linter rule (R-ATL-NEW-01) → Negative test (duplicate_task_ids.md)

**Deliverable (if time permits):**
Create `docs/TRACEABILITY_MATRIX.md`:
| Spec Requirement | Rule ID | Test Fixture | Status |
|------------------|---------|--------------|--------|
| "MUST use $-prefix" | R-ATL-075 | negatives/bad_var.md | ✅ |
| "MUST have unique IDs" | R-ATL-NEW-01 | negatives/dup_ids.md | 🚧 |

**Purpose:** Catch coverage gaps (requirement without rule, rule without test).
8. Step 1 "Add/update negatives" Too Vague
Line 29: Which negatives? Where? New or modify existing?
Be specific:
markdown### 1) Linter (Detailed Changes)

**R-ATL-022 changes:**
- Modify: `check_evidence_blocks()` function (line 456)
- Add parameter: `mode: Literal["plan", "instantiated"]`
- Logic: If mode=="plan", skip placeholder check; if mode=="instantiated", enforce strict

**New negatives to create:**
1. `validation/negatives/instantiated_with_placeholder.md`
   - Triggers: R-ATL-022 (evidence placeholder in instantiated)
   - Error: "Evidence placeholder [[PH:OUTPUT]] forbidden in instantiated mode"

2. `validation/negatives/duplicate_task_ids.md`
   - Triggers: R-ATL-NEW-01 (task 1.1 defined twice)
   - Error: "Duplicate task ID '1.1' found at lines 45 and 230"

3. `validation/negatives/coverage_phantom_refs.md`
   - Triggers: R-ATL-NEW-02 (references task 2.1 that doesn't exist)
   - Error: "Coverage references task '2.1' which does not exist"

**Existing negatives to verify still fail:**
- `validation/negatives/plan_forbidden_$var.md` (R-ATL-075 still triggers)
9. Validation Phase B Output Format Unclear
Line 48: "update results in VALIDATION_SUITE.md" - What format?
Specify:
markdown### 4) Validation (Phase B - Post-Fix)

**Run full suite:**
```bash
$ python run_validation_suite.py --verbose > validation/post_fix_results.txt
```

**Update VALIDATION_SUITE.md:**
Add results table:
| Test Type | Pre-Fix (Baseline) | Post-Fix | Status |
|-----------|-------------------|----------|--------|
| Positives | 23/25 pass | 25/25 pass | ✅ Fixed |
| Negatives | 18/20 fail (correct) | 22/22 fail (correct) | ✅ Stronger |
| Canaries | 10/10 pass | 10/10 pass | ✅ No regression |

**Append changelog entry:**
```
## 2024-XX-XX - GENERAL_FIX_1 Results
- R-ATL-022: Plan mode evidence placeholders now allowed
- R-ATL-NEW-01: Unique task ID enforcement added
- R-ATL-NEW-02: Coverage reference resolution added
- Validation: All positives pass; all negatives fail correctly; no canary regressions
```
10. Regression Prevention Needs Ownership
Line 63: "require spec+linter co-change review checklist" - Who enforces? When? How?
Add:
markdown## Regression Prevention (Enforcement)

### New CI Checks (Automated)
1. **tests/test_spec_examples.py** (added in Step 5)
   - Runs: On every PR to `main`
   - Validates: All code blocks in spec pass linter
   - Blocks merge: If any spec example invalid

2. **tests/test_rule_consistency.py** (added in Step 5)
   - Runs: On every PR touching linter or spec
   - Validates: Rule IDs in spec exist in linter code
   - Blocks merge: If rule documented but not implemented

### Review Checklist (Manual, Required for PRs)
**For any PR modifying linter OR spec:**
- [ ] Updated both linter AND spec together (no solo changes)
- [ ] Ran `test_spec_examples.py` locally (all pass)
- [ ] Ran `test_rule_consistency.py` locally (all pass)
- [ ] Added/updated relevant test fixtures (positives/negatives)
- [ ] Updated COMMON.md if user-facing behavior changed
- [ ] Regenerated template examples if affected

**Reviewer:** Tech lead must verify checklist before approval

**Ownership Matrix:**
| Artifact | Owner (Changes) | Reviewer (Approval) |
|----------|----------------|---------------------|
| Linter | Any dev | Tech lead |
| Spec | Any dev | Tech lead |
| COMMON | Doc lead | Tech lead |
| Template | Doc lead | Any dev |

WHAT'S STILL GOOD ✅

Goal #3 (Internal consistency) - Directly addresses PYDANTIC_SCHEMA phantom references
Version semantics - Clear spec vs. schema explanation
Change Impact/Order - Dependency chain prevents ordering bugs
Two-phase validation - Baseline comparison catches regressions
Rollback awareness - Shows you're thinking about failure modes
Framework focus - Not trying to fix specific docs, just the ruleset


MINIMUM VIABLE FIXES (Priority Order)
P0 - Blocking (Required Before Approval):

Fill Current State Audit - Create BASELINE_AUDIT.md with actual evidence (3 sections: drift examples, coverage phantoms, validation baseline)
Define rules inline - Add table with R-ATL-022, R-ATL-075, NEW-01, NEW-02 definitions
Add artifact inventory - Complete file path list with checkboxes
Make DoD testable - Replace "agree/aligned/passes" with specific bash commands

P1 - High Risk:
5. Specify new negative fixtures - Explicit list of 3 new files to create
6. Detail rollback canaries - Identify 10 specific docs to test against
7. Clarify Goal #5 - Either expand requirement anchors or delete "stretch"
8. Add ownership to prevention - Who reviews, who merges, who enforces
P2 - Quality:
9. Expand Step 1 details - Show code changes, not just "update linter"
10. Format validation output - Show exact table structure for VALIDATION_SUITE.md update

ANSWER: Is This Plan Viable Now?
Framework focus: ✅ EXCELLENT - You're attacking systemic drift, not patching individual docs
Execution readiness: 75% complete (up from 60%)
Remaining blockers:

Current State Audit is still a template (needs actual evidence)
Rule definitions still missing (what do R-ATL-* check today?)
Artifact inventory still missing (can't verify files exist)
Definition of Done still too vague (needs commands, not prose)

Recommendation:
STOP and complete P0 items before any implementation. You're 80% there, but the missing 20% is load-bearing. Without baseline evidence, you can't prove success. Without rule definitions, developers can't implement. Without file paths, you can't verify completeness.
The plan is structurally sound but informationally incomplete. It's ready for "Phase 0: Baseline Collection" but not ready for Step 1 (Linter changes) until P0 items complete.
Transform "evidence needed" from TODO into actual data, and this becomes executable.
