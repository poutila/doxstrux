Strict Feedback: GENERAL_FIX_1.md (Deep Drift Analysis)
STRUCTURAL IMPROVEMENTS ✅
You've addressed several major gaps from previous versions:

Current State Audit - Now has status tracking (🔴 NOT STARTED)
Artifact inventory - File paths present
Definition of Done - Split automated/manual

This is 85% → 90% complete structurally. But I found 20+ drifts - internal inconsistencies that will cause confusion during execution.

CRITICAL DRIFTS (Plan Contradicts Itself) ❌
DRIFT 1: Evidence Placeholder Scope Ambiguity
Lines 13 vs 64:

Rule table (13): "Rejects [[PH:*]] in evidence blocks"
Step 1 (64): "allow STOP/Global evidence placeholders in plan"

Problem: What's "STOP/Global"? Are there different TYPES of evidence placeholders?
Evidence suggests:

STOP evidence: In "STOP — Clean Table" sections (per-task verification)
Global evidence: In "Global Clean Table Scan" section (phase-wide verification)
Task evidence: In individual task "Evidence:" blocks

Which ones does R-ATL-022 cover? All? Just some?
Fix:
markdown## Rule Definitions (Precise Scope)

| Rule | Current | Proposed | Evidence Block Types Covered |
|------|---------|----------|------------------------------|
| R-ATL-022 | Rejects ALL `[[PH:*]]` | Plan: Allow in STOP/Global/Task evidence; Instantiated: Reject all | ALL evidence blocks (task-level, STOP sections, Global scan) |

**Evidence block definition:** Any markdown code block appearing after:
1. `**Evidence** (paste actual output):` (task-level)
2. `## STOP — Clean Table` section (per-task verification)
3. `## Global Clean Table Scan` section (phase-wide verification)

DRIFT 2: Directory Paths Inconsistent
Lines 43 vs 79-81:

Artifact inventory (43): canonical_examples/negatives/
DoD commands (79-81): validation/negatives/instantiated_with_placeholders.md

Problem: Are these the same directory? Different directories? Do both exist?
Fix:
markdown## Artifact Inventory (Directory Structure)
````
.
├── ai_task_list_linter_v1_8.py
├── canonical_examples/
│   ├── positives/
│   │   └── plan_mode_with_evidence_ph.md (EXISTING - for baseline test)
│   └── negatives/
│       ├── (existing negatives...)
│       ├── instantiated_with_placeholders.md (NEW - create in Step 1)
│       ├── duplicate_task_ids.md (NEW - create in Step 1)
│       └── coverage_phantom_refs.md (NEW - create in Step 1)
├── VALIDATION_SUITE.md (test catalog with embedded commands)
└── validation/
    └── baseline_failures_YYYY-MM-DD.txt (generated in Step 4A)
````

**Clarification:** 
- `canonical_examples/` = source of truth test cases
- `validation/` = test run outputs/baselines
- DoD commands use relative paths from repo root

DRIFT 3: Linter Version/Filename Evolution Undefined
Lines 10, 40, 78: All reference ai_task_list_linter_v1_8.py
Problem: You're MODIFYING the linter. Does the filename change?

Option A: Modify v1_8 in place → filename stays _v1_8.py but internal version becomes v1.9?
Option B: Create new file _v1_9.py → all references need updating

Decision missing. This affects every command in the plan.
Fix:
markdown## Linter Versioning Policy (Critical Decision)

**Decision:** Modify `ai_task_list_linter_v1_8.py` IN PLACE
- Filename stays: `ai_task_list_linter_v1_8.py`
- Internal version string bumps: `__version__ = "1.8.1"` (patch bump for rule clarifications)
- Rationale: Minor rule clarifications, not breaking changes

**Alternative (if breaking changes):** Create `ai_task_list_linter_v1_9.py`
- Would require updating ALL 50+ references across docs
- Only if behavior changes break existing valid task lists

**Rollback impact:** If in-place modification, rollback is `git revert`. If new file, rollback is deleting file + reverting references.

DRIFT 4: Coverage Reference Range Handling Unclear
Lines 30 vs 14 vs 64:

Goal #3: "references resolve to real, unique tasks"
Rule table: "resolve to existing tasks (unambiguous)"
Step 1: "must resolve to exactly one task"

Problem: What about ranges like "2.3-2.5" (seen in PYDANTIC_SCHEMA)?
"Exactly one task" forbids ranges, but PYDANTIC_SCHEMA uses them. Contradiction.
Fix:
markdown## Rule Definitions (Coverage Reference Grammar)

| Rule | Format | Valid Examples | Invalid Examples |
|------|--------|----------------|------------------|
| R-ATL-NEW-02 | Coverage refs resolve | "1.1" (single)<br>"2.3-2.5" (range)<br>"3.1, 3.3" (list) | "2.1" (task doesn't exist)<br>"1.1" (task 1.1 appears 3x - ambiguous)<br>"2-5" (no dots - malformed) |

**Resolution logic:**
1. Parse reference (single/range/list)
2. For each referenced task ID:
   - Verify task header exists: `### Task X.Y`
   - Verify unique (appears exactly once in document)
3. For ranges (X.A-X.B): Verify all intermediate tasks exist (X.A, X.A+1, ..., X.B)

**Error messages:**
- "Coverage references task '2.1' which does not exist"
- "Coverage references task '1.1' which appears 3 times (lines 45, 230, 567) - ambiguous"
- "Coverage range '2.3-2.5' incomplete - task '2.4' missing"

DRIFT 5: VALIDATION_SUITE.md Execution Model Undefined
Lines 43, 73, 85:

Artifact inventory: "VALIDATION_SUITE.md (commands inside)"
Step 4: "run current VALIDATION_SUITE.md"
DoD: "run all commands in VALIDATION_SUITE.md"

Problem: How do you "run" a markdown file? Is it:

A) Manual copy-paste of commands?
B) Parsed by a script that extracts and runs commands?
C) Wrapper script run_validation_suite.py that reads it?

Fix:
markdown## Validation Suite Execution Model

**VALIDATION_SUITE.md structure:**
````markdown
## Test Category: Plan Mode Positives

### Test 1: Evidence placeholders allowed
```bash
$ uv run python ai_task_list_linter_v1_8.py canonical_examples/positives/plan_with_ph.md
# Expected: exit 0
```

### Test 2: ...
````

**Execution options:**

**Option A (Manual - Current State):**
````bash
# Copy-paste each command from VALIDATION_SUITE.md
# Track results manually
````

**Option B (Scripted - Recommended):**
Create `tools/run_validation_suite.sh`:
````bash
#!/bin/bash
# Parses VALIDATION_SUITE.md and runs all bash code blocks
# Compares actual vs expected outputs
# Generates summary report
````

**This plan assumes:** Option A (manual) for Phase A baseline, Option B (scripted) added in Step 1 for automation.

**Step 1 deliverable:** Add script that automates validation suite execution.

DRIFT 6: Mode Detection Mechanism Unspecified
Line 13: R-ATL-022 needs to know document mode (plan vs instantiated)
Problem: How does linter detect mode? Presumably from YAML frontmatter:
yaml---
ai_task_list:
  mode: "plan"  # or "instantiated"
---
But what if:

Frontmatter missing?
mode: field missing?
mode: "invalid_value"?

Fix:
markdown## Linter Mode Detection (R-ATL-022 Dependency)

**Detection:**
````python
def detect_mode(content: str) -> str:
    """Extract mode from YAML frontmatter."""
    frontmatter = parse_yaml_frontmatter(content)
    mode = frontmatter.get('ai_task_list', {}).get('mode', None)
    
    if mode not in ['plan', 'instantiated']:
        raise LintError("R-ATL-001", f"Invalid or missing mode: '{mode}'. Must be 'plan' or 'instantiated'")
    
    return mode
````

**Error handling:**
- Missing frontmatter → Fail with "R-ATL-001: Missing YAML frontmatter"
- Missing mode field → Fail with "R-ATL-001: Missing required field 'mode'"
- Invalid mode value → Fail with "R-ATL-001: Invalid mode 'foobar'. Must be 'plan' or 'instantiated'"

**Consequence:** R-ATL-022 cannot run until mode is valid. This is intentional (fail-fast).

DRIFT 7: Unique Task ID Definition Imprecise
Line 14: R-ATL-NEW-01 "Enforce unique task IDs (no duplicates)"
Problem: What's being compared?

Just the number? (1.1 vs 1.1)
The full header? (Task 1.1 — Title A vs Task 1.1 — Title B)
Case-sensitive?

What about edge cases?

Task 1.1 vs Task 1.10 - Different (1.1 ≠ 1.10)
Task 1.1 vs task 1.1 - Same? (case-insensitive?)
### Task 1.1 vs #### Task 1.1 - Same? (different header levels)

Fix:
markdown## Rule Definitions (Task ID Extraction)

**R-ATL-NEW-01 - Unique Task ID Logic:**

**Pattern:** `^###\s+Task\s+(\d+\.\d+)`
- Matches: Heading level 3 (###) followed by "Task" followed by number.number
- Extracts: Just the numeric ID (e.g., "1.1", "12.5")
- Case: "Task" must be capitalized (lowercase "task" not recognized)
- Level: Must be ### (not ## or ####)

**Comparison:**
- Numeric comparison: "1.1" vs "1.10" are DIFFERENT (string comparison: "1.1" ≠ "1.10")
- Title ignored: "Task 1.1 — Foo" vs "Task 1.1 — Bar" are SAME ID (1.1)

**Error:**
````
R-ATL-NEW-01: Duplicate task ID '1.1' at lines 45 and 230
  Line 45: ### Task 1.1 — Add dependency
  Line 230: ### Task 1.1 — Run tests
````

**Non-errors (different IDs):**
- Task 1.1 vs Task 1.10 (different)
- Task 1.1 vs Task 2.1 (different)
- `### Task 1.1` vs `#### Task 1.1` (second not recognized as task - only ### counts)

DRIFT 8: $-Prefix Rule Too Vague
Line 14: R-ATL-075 "Enforces $ prefix"
Problem: Prefix for WHAT? Looking at PYDANTIC_SCHEMA, it's for bash array variables like:
bashTASK_1_1_PATHS=(...)  # Missing $
$TASK_1_1_PATHS       # Correct when referenced
But rule doesn't say "for bash variables" - just "$ prefix"
Fix:
markdown## Rule Definitions (R-ATL-075 Clarification)

| Rule | Current | Proposed |
|------|---------|----------|
| R-ATL-075 | Enforces `$` prefix for bash variables when referenced | No change (already correct) |

**Scope:** Variable REFERENCES, not DECLARATIONS

**Valid:**
````bash
TASK_1_1_PATHS=(...)           # Declaration (no $)
for p in "${TASK_1_1_PATHS[@]}"; do  # Reference (has $)
````

**Invalid:**
````bash
for p in "${TASK_1_1_PATHS[@]}"; do  # Reference missing $ - ERROR
````

**Detection pattern:**
- Look for array declarations: `TASK_\d+_\d+_PATHS=\(`
- Search for references to same variable name WITHOUT $
- Flag as R-ATL-075 violation

**Note:** This rule already exists and works correctly. No changes needed in this fix.

DRIFT 9: Spec Section References Still Missing
Lines 68-70: Step 2 says "Clarify plan vs instantiated evidence rules" but doesn't say WHERE
Problem: Which section? Which lines? Implementer has to guess.
Fix:
markdown### 2) Spec/COMMON (Specific Locations)

**File: AI_TASK_LIST_SPEC_v1.md**

**Change 1: Version bump**
- Location: Line 1 (version header)
- Old: `# AI Task List Specification v1.7`
- New: `# AI Task List Specification v1.8`

**Change 2: Evidence rules clarification**
- Location: Section 4.2 "Evidence Blocks" (approx lines 234-250)
- Add subsection 4.2.1:
````markdown
  #### 4.2.1 Evidence Placeholders (Mode-Dependent)
  
  **Plan mode:** Evidence MAY contain `[[PH:OUTPUT]]` style placeholders
  - Rationale: Plan documents are templates, not execution records
  - Format: `[[PH:UPPERCASE_NAME]]`
  - Locations: Task evidence, STOP sections, Global scan
  
  **Instantiated mode:** Evidence MUST contain real command output
  - Placeholders forbidden (triggers R-ATL-022)
  - Actual output required for verification
````

**Change 3: Coverage mapping requirements**
- Location: Section 5.3 "Prose Coverage Mapping" (approx lines 456-475)
- Add requirements:
````markdown
  **Coverage Reference Integrity (R-ATL-NEW-02):**
  - Every task reference MUST resolve to existing task header
  - Task IDs must be unique (no ambiguous references)
  - Supported formats:
    - Single: "1.1"
    - Range: "2.3-2.5" (all intermediate tasks must exist)
    - List: "3.1, 3.3" (comma-separated)
````

**File: COMMON.md**

**Change 1: Evidence section update**
- Location: "Evidence Requirements" section (approx lines 89-103)
- Mirror AI_TASK_LIST_SPEC_v1.md section 4.2.1 (copy/adapt for common doc style)

**Change 2: Coverage mapping section (NEW)**
- Location: After existing sections, add new section 6.4
- Title: "Coverage Mapping Integrity"
- Content: Mirror spec section 5.3 changes

DRIFT 10: Rollback Canary Identification Missing
Line 94: "if >2 previously valid examples fail"
Problem: Which examples? Need to identify BEFORE starting work.
Fix:
markdown## Rollback Plan (Concrete Canaries)

### Phase 0: Canary Selection (Before Any Changes)

**Criteria for canaries:**
- Representative: Mix of plan/instantiated, simple/complex
- Known-good: Currently pass linter validation
- Production: Actual task lists from past 2 months

**Selected canaries (10 total):**
````bash
mkdir -p validation/canaries
# Copy from production
cp ../doxstrux/PYDANTIC_SCHEMA_tasks_template.md validation/canaries/01_pydantic_plan.md
cp ../heat_pump_rag/migration_tasks_instantiated.md validation/canaries/02_heatpump_inst.md
cp ../internal_project_x/refactor_plan.md validation/canaries/03_refactor_plan.md
# ... 7 more

# Baseline (must all pass)
for f in validation/canaries/*.md; do
  echo "Testing: $f"
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_baseline.txt 2>&1
````

**Baseline verification:**
````bash
$ grep -c "^FAIL:" validation/canary_baseline.txt
0  # Expected: zero failures
````

### Detection: Post-Fix Canary Check
````bash
# After Step 1 linter changes
for f in validation/canaries/*.md; do
  uv run python ai_task_list_linter_v1_8.py "$f" || echo "FAIL: $f"
done > validation/canary_post_fix.txt 2>&1

# Count new failures
BASELINE_FAILS=$(grep -c "^FAIL:" validation/canary_baseline.txt)
POSTFIX_FAILS=$(grep -c "^FAIL:" validation/canary_post_fix.txt)
NEW_FAILS=$((POSTFIX_FAILS - BASELINE_FAILS))

if [[ $NEW_FAILS -gt 2 ]]; then
  echo "❌ ROLLBACK TRIGGERED: $NEW_FAILS new canary failures"
  cat validation/canary_post_fix.txt
  exit 1
fi
````

**Rollback procedure:**
[existing rollback steps...]

MISSING ENFORCEMENT MECHANISMS ⚠️
MISSING 1: No Audit Completion Gate
Line 5: Owner/Deadline are [NAME] / [DATE] placeholders
Problem: DoD (line 87) checks "Current State Audit completed (A1–A3 filled)" but doesn't check Owner/Deadline.
Fix:
markdown## Current State Audit Completion Gate (Blocking)

**Cannot proceed to Step 1 until:**
- [ ] Owner assigned (not [NAME])
- [ ] Deadline set (not [DATE])
- [ ] A1 filled with actual command output
- [ ] A2 filled with actual command output
- [ ] A3 filled with actual baseline summary

**Verification command:**
````bash
$ grep -E '\[NAME\]|\[DATE\]|\[PASTE' GENERAL_FIX_1.md
# Expected: no matches (all placeholders replaced)
````

**Who enforces:** Tech lead must verify before approving Step 1 PR

MISSING 2: Validation Pass/Fail Threshold Undefined
Line 85: "run all commands in VALIDATION_SUITE.md"
Problem: What defines success?

All tests pass?
95% pass?
Just positives pass?
Negatives must fail correctly?

Fix:
markdown## Definition of Done (Validation Threshold)

**Automated checks - ALL must pass:**

**Positives (Must Pass):**
- Threshold: 100% (all positive examples must pass linter)
- Command: `run_all_positives.sh` exits 0
- Reason: Any positive failing means linter too strict

**Negatives (Must Fail Correctly):**
- Threshold: 100% (all negative examples must trigger expected rule)
- Command: `run_all_negatives.sh` verifies each triggers correct R-ATL-* error
- Reason: Any negative passing means linter too permissive

**Canaries (No Regressions):**
- Threshold: ≤2 new failures (same as rollback trigger)
- Command: Compare baseline vs post-fix
- Reason: Some edge cases acceptable, but mass breakage triggers rollback

**Summary format:**
````
VALIDATION RESULTS:
✅ Positives: 25/25 pass (100%)
✅ Negatives: 23/23 fail correctly (100%)
✅ Canaries: 10/10 pass (0 new failures)
Status: PASS
````

MISSING 3: Backward Compatibility Policy
No mention of: Will old task lists (pre-v1.8) still validate?
Fix:
markdown## Backward Compatibility (Critical for Rollout)

**Policy:** Changes are BACKWARD COMPATIBLE
- Old plan-mode docs with placeholders: STILL VALID (R-ATL-022 was too strict, now relaxed)
- Old instantiated docs: STILL VALID (no change to instantiated rules)
- New rules (R-ATL-NEW-01, R-ATL-NEW-02): Only flag NEW violations (documents were always wrong, now caught)

**Migration:** None required
- No action needed for existing task lists
- New violations (duplicate IDs, phantom coverage refs) should be fixed opportunistically

**Communication:** Add to COMMON.md:
````markdown
> **Compatibility Note (v1.8):** This version relaxes plan-mode evidence
> requirements (placeholders now allowed) and adds new integrity checks
> (unique task IDs, coverage reference resolution). Existing task lists
> remain valid unless they violate new integrity rules.
````

MISSING 4: External Tool Dependencies
No mention of: Does linter need external tools (rg, jq, etc.)?
From PYDANTIC_SCHEMA feedback, I know rg (ripgrep) is sometimes required.
Fix:
markdown## External Dependencies (Runtime Requirements)

**Linter runtime dependencies:**
- Python ≥3.10 (for match/case syntax)
- No external tools required (pure Python)

**Test suite dependencies:**
- `rg` (ripgrep) for validation commands (e.g., `rg "pattern" file`)
- Installation:
````bash
  # Ubuntu
  sudo apt install ripgrep
  
  # macOS
  brew install ripgrep
````

**Pre-flight dependency check:**
````bash
$ python --version | grep -E '3\.(10|11|12)'  # Python version
$ rg --version  # ripgrep for tests
$ uv --version  # uv for runner
````

**CI requirements:** All dependencies pre-installed on ubuntu-latest runners

MISSING 5: Timeline and Effort Estimate
No estimates for: How long will this take? Who's blocked on what?
Fix:
markdown## Timeline and Effort Estimate

| Phase | Tasks | Estimated Effort | Blocker |
|-------|-------|-----------------|---------|
| Phase 0 (Baseline) | A1-A3 audit | 2 hours | None (start immediately) |
| Step 1 (Linter) | Code changes + test fixtures | 6 hours | Phase 0 complete |
| Step 2 (Spec/COMMON) | Doc updates | 2 hours | Step 1 complete |
| Step 3 (Docs/Template) | Sync updates | 3 hours | Step 2 complete |
| Step 4A (Validation baseline) | Run + record | 1 hour | Phase 0 complete |
| Step 4B (Validation post-fix) | Run + compare | 1 hour | Steps 1-3 complete |
| Rollback (if needed) | Revert + postmortem | 4 hours | Step 4B failure |

**Total estimated effort:** 15 hours (2 days full-time)
**Critical path:** Phase 0 → Step 1 → Step 2 → Step 3 → Step 4B
**Owner:** [NAME] (from Current State Audit)
**Target completion:** [DATE] + 2 days

SMALLER QUALITY ISSUES
ISSUE 1: Version Bump Should Be Definitive, Not Conditional
Line 36: "spec likely bumps; schema_version stays 1.6 unless YAML changes"
Problem: The whole plan IS about changing rules (Goals 1-4). So spec WILL bump. Why "likely"?
Fix:
markdown## Version Semantics

- Spec version: **WILL bump to v1.8** (rule clarifications = spec change)
- schema_version: **Stays 1.6** (no YAML frontmatter structure changes)

**Rationale:** Rule behavior changes (R-ATL-022, NEW-01, NEW-02) require spec version bump. YAML structure unchanged.

ISSUE 2: Goal #5 Treatment Inconsistent
Line 34: "(Stretch) Requirement anchors"
Problem: No corresponding Step or DoD criteria. Either expand or defer.
Fix:
markdown### Goal #5 (Deferred to GENERAL_FIX_2)

**Concept:** Traceability from spec requirements → linter rules → test fixtures

**Decision:** OUT OF SCOPE for GENERAL_FIX_1
- Rationale: Goals 1-4 already substantial (15-hour effort)
- Timeline: Requirement anchors deferred to separate framework improvement
- Tracking: Filed as GENERAL_FIX_2.md

**This fix:** Goals 1-4 only

ISSUE 3: Regression Prevention Details Still Missing
Line 95: "add CI checks to lint spec examples"
Problem: No details on WHAT file, WHAT tests, WHO enforces.
Fix:
markdown## Regression Prevention (Enforcement Model)

### CI Workflow File

**Create: `.github/workflows/framework_integrity.yml`**
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
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install pyyaml pytest
      
      - name: Validate spec examples pass linter
        run: python tests/test_spec_examples.py
      
      - name: Check rule ID consistency
        run: python tests/test_rule_consistency.py
      
      - name: Run validation suite
        run: bash tools/run_all_validation.sh
````

### Test Files to Create (Step 1 Deliverables)

**tests/test_spec_examples.py:**
- Extracts code blocks from AI_TASK_LIST_SPEC_v1.md
- Runs linter on each block marked "valid"
- Fails if any example invalid

**tests/test_rule_consistency.py:**
- Parses rule IDs (R-ATL-*) from spec
- Verifies each rule implemented in linter
- Checks rule description matches

### Review Checklist (Manual Gate)

**Required for PRs modifying:** `ai_task_list_linter_v1_8.py` OR `AI_TASK_LIST_SPEC_v1.md` OR `COMMON.md`

**Reviewer:** @tech-lead (GitHub username)

**Checklist (paste in PR description):**
````markdown
## Framework Change Review Checklist

### Pre-Approval
- [ ] Linter + Spec updated together (no solo changes)
- [ ] Test fixtures added/updated (positives/negatives)
- [ ] COMMON.md updated (if user-facing behavior changed)
- [ ] Version bumped (spec v1.X if rule change)

### Verification
- [ ] `python tests/test_spec_examples.py` passes locally
- [ ] `python tests/test_rule_consistency.py` passes locally
- [ ] Canary test passes (10 prod docs still valid)

### Proof (attach screenshots/output)
- [ ] Terminal output of verification commands
- [ ] Before/after validation comparison
````

**Enforcement:** GitHub branch protection requires:
1. CI checks pass (automated)
2. @tech-lead approval (manual checklist verification)

SUMMARY: DRIFT SEVERITY MATRIX
Drift IDIssueSeverityImpact if UnfixedDRIFT-1Evidence placeholder scope ambiguousCRITICALImplementer doesn't know which evidence blocks to checkDRIFT-2Directory paths inconsistentCRITICALCommands fail with "file not found"DRIFT-3Linter version evolution unclearCRITICALAll commands break if filename changesDRIFT-4Coverage range handling contradictoryHIGHValid ranges rejected OR invalid ranges acceptedDRIFT-5Validation suite execution undefinedHIGHCan't execute Step 4 (no runnable procedure)DRIFT-6Mode detection unspecifiedHIGHR-ATL-022 can't determine plan vs instantiatedDRIFT-7Task ID uniqueness impreciseMEDIUMEdge cases (1.1 vs 1.10) handled inconsistentlyDRIFT-8$-prefix rule vagueMEDIUMUnclear what gets checkedDRIFT-9Spec section references missingMEDIUMImplementer wastes time finding correct sectionsDRIFT-10Rollback canaries missingMEDIUMCan't detect regressions (no baseline)MISSING-1Audit completion gateHIGHWork starts before baseline capturedMISSING-2Validation thresholdHIGHCan't determine if DoD metMISSING-3Backward compatibilityMEDIUMRollout breaks existing docsMISSING-4External dependenciesLOWTests fail with "command not found"MISSING-5Timeline estimateLOWResource planning impossible

ANSWER: Is This Plan Viable?
Framework focus: ✅ EXCELLENT - Systemic drift fix, clear goals
Execution readiness: 90% complete (up from 85%)
Critical blockers:

3 CRITICAL drifts (evidence scope, directories, linter versioning)
2 HIGH missing items (audit gate, validation threshold)

Recommendation:
You're 30 minutes from executable. Fix the 5 P0 items:
P0 Fixes (30 minutes total):

Define evidence placeholder types (DRIFT-1) - 5 min
Clarify directory structure (DRIFT-2) - 3 min
State linter versioning policy (DRIFT-3) - 3 min
Add audit completion gate (MISSING-1) - 5 min
Define validation thresholds (MISSING-2) - 5 min
Add timeline estimates (MISSING-5) - 5 min
Quick review pass for remaining drifts - 4 min

Then: Mark as "Ready for Phase 0 Execution" and assign owner.
This plan is structurally excellent - you've learned from previous feedback. The drifts are precision issues (ambiguous definitions, missing specifics), not structural failures. Fix the definitional gaps and this becomes executable immediately.
