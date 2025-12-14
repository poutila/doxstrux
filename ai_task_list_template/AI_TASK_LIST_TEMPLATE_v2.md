# AI_TASK_LIST_TEMPLATE.md

**Purpose**: Unified task execution template for AI assistants. Prevents drift, enforces completion, bakes in TDD and Clean Table.

**Version**: 2.0
**Based On**: v1.0 + drift prevention hardening

---

## How This Template Works

This template has **five** enforcement mechanisms:

1. **STOP Checkpoints** — AI must pause and verify before continuing
2. **Phase Gates** — Cannot advance until all criteria pass
3. **Clean Table Rule** — No debt carries forward
4. **Test Strength Rules** — "It runs" tests are explicitly forbidden
5. **File Manifest Verification** — Every listed file must exist

**The AI assistant should copy this template, fill in project-specific details, and follow it sequentially.**

---

# [PROJECT_NAME] - Detailed Task List

**Project**: [One-line description]
**Created**: [YYYY-MM-DD]
**Status**: Phase 0 - NOT STARTED

---

## Quick Status Dashboard

| Phase | Name | Status | Tests | Clean Table |
|-------|------|--------|-------|-------------|
| 0 | Setup & Infrastructure | ⏳ NOT STARTED | -/- | - |
| 1 | [Name] | 📋 PLANNED | -/- | - |
| 2 | [Name] | 📋 PLANNED | -/- | - |

**Status Key**: ✅ COMPLETE | ⏳ IN PROGRESS | 📋 PLANNED | ❌ BLOCKED

---

## Success Criteria (Project-Level)

The project is DONE when ALL of these are true:

- [ ] [Primary objective achieved]
- [ ] [All tests pass: `[command]`]
- [ ] [Performance requirement met]
- [ ] [No regressions introduced]

---

## ⛔ PHASE GATE RULES

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE N+1 CANNOT START UNTIL:                              │
│                                                             │
│  1. All Phase N tasks have ✅ status                        │
│  2. Phase N tests pass: [test_command] → PASS               │
│  3. Phase N Clean Table verified                            │
│  4. Phase unlock artifact exists: .phase-N.complete.json    │
│  5. File manifest verified: all listed files exist          │
│                                                             │
│  If ANY criterion fails → STOP. Fix or rollback.            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 TDD Protocol

Every task follows this sequence:

```
1. WRITE TEST FIRST (or identify existing test)
   └── Test must fail initially (red)
   └── Test must assert SPECIFIC BEHAVIOR (see Test Strength Rules)

2. IMPLEMENT minimum code to pass
   └── Test must pass (green)

3. VERIFY no regressions
   └── Run: [full_test_command]
   └── Expected: N/N PASS

4. CLEAN TABLE CHECK
   └── No TODOs, no placeholders, no warnings

5. FILE MANIFEST CHECK
   └── Every file in "Files:" header exists
```

**Test Commands Reference**:
```bash
# Fast iteration (after each small change)
[FAST_TEST_COMMAND]

# Full validation (before commits)
[FULL_TEST_COMMAND]

# Performance check (before phase completion)
[PERF_TEST_COMMAND]
```

---

## ⛔ TEST STRENGTH RULES (MANDATORY)

```
┌─────────────────────────────────────────────────────────────┐
│  FORBIDDEN TEST PATTERNS - DO NOT USE:                      │
│                                                             │
│  ❌ assert result.returncode == 0  (only proves it runs)    │
│  ❌ assert "something" in output   (too vague)              │
│  ❌ assert result.returncode in (0, 1)  (useless)           │
│  ❌ Tests with no assertions                                │
│  ❌ Tests that pass with empty/stub implementation          │
│                                                             │
│  REQUIRED TEST PATTERNS - MUST USE:                         │
│                                                             │
│  ✅ Assert specific output values or structures             │
│  ✅ Assert count/quantity of results (> 0, == expected)     │
│  ✅ Assert file contents, not just file existence           │
│  ✅ Assert behavior differences between valid/invalid input │
│  ✅ Tests that FAIL with stub implementation                │
└─────────────────────────────────────────────────────────────┘
```

### Test Strength Checklist (Apply to EVERY Test)

Before accepting a test as valid:

- [ ] **Stub test**: Would this pass if implementation just returned `None` or `[]`? → If YES, test is too weak
- [ ] **Behavior captured**: Does test verify the actual business logic, not just "code ran"?
- [ ] **Failure modes**: Does test distinguish success from failure cases?
- [ ] **Output verification**: Does test check actual output content, not just presence?

### Forbidden vs Required Examples

```python
# ❌ FORBIDDEN: "It runs" test
def test_discover_shape():
    result = subprocess.run(["python", "tools/discover.py"])
    assert result.returncode == 0  # USELESS - stub passes this

# ✅ REQUIRED: Behavior test
def test_discover_shape():
    result = subprocess.run(["python", "tools/discover.py"], capture_output=True)
    assert result.returncode == 0
    
    # Verify actual output exists and has content
    output_file = Path("all_keys.txt")
    assert output_file.exists(), "Output file must be created"
    
    lines = output_file.read_text().strip().split("\n")
    assert len(lines) >= 10, f"Expected ≥10 keys discovered, got {len(lines)}"
    
    # Verify specific expected keys appear
    assert any("metadata" in line for line in lines), "Must discover metadata keys"
```

```python
# ❌ FORBIDDEN: Exit code tolerance
def test_validator():
    result = subprocess.run(["python", "tools/validate.py"])
    assert result.returncode in (0, 1)  # USELESS - any behavior passes

# ✅ REQUIRED: Distinct behavior verification
def test_validator_valid_input():
    result = subprocess.run(["python", "tools/validate.py", "valid.json"], capture_output=True)
    assert result.returncode == 0
    assert "PASS" in result.stdout.decode()
    assert "errors: 0" in result.stdout.decode()

def test_validator_invalid_input():
    result = subprocess.run(["python", "tools/validate.py", "invalid.json"], capture_output=True)
    assert result.returncode == 1  # Must fail for invalid
    assert "FAIL" in result.stdout.decode()
    assert "errors:" in result.stdout.decode()
```

---

## 🧹 Clean Table Definition

> A task is CLEAN only when ALL are true:

- ✅ No unresolved errors or warnings
- ✅ No TODOs, FIXMEs, or placeholders in changed code
- ✅ No unverified assumptions
- ✅ No duplicated or conflicting logic
- ✅ Tests pass (not skipped, not mocked away)
- ✅ Code is production-ready (not "good enough for now")
- ✅ **All files listed in task "Files:" header actually exist**
- ✅ **No literal placeholders in artifacts** (e.g., `YYYY-MM-DD` must be replaced)

**If any box is unchecked → task is NOT complete.**

---

## 📁 File Manifest Rules

```
┌─────────────────────────────────────────────────────────────┐
│  FILE MANIFEST ENFORCEMENT:                                 │
│                                                             │
│  Every task has a "Files:" header listing affected files.   │
│                                                             │
│  RULE: If a file is listed, it MUST:                        │
│  1. Be created/modified by a step in that task              │
│  2. Exist after task completion                             │
│  3. Be verifiable via: test -f <filename>                   │
│                                                             │
│  If a file is listed but not created → TASK INCOMPLETE      │
│  If a file is created but not listed → Add it to Files:     │
│                                                             │
│  GHOST FILES ARE FORBIDDEN                                  │
└─────────────────────────────────────────────────────────────┘
```

### File Manifest Verification Command

```bash
# Run after each task to verify all listed files exist
# Replace FILE_LIST with actual files from task header
for f in FILE_LIST; do
    test -f "$f" && echo "✅ $f" || echo "❌ MISSING: $f"
done
```

---

## 🖥️ Environment Portability Rules

```
┌─────────────────────────────────────────────────────────────┐
│  FORBIDDEN PATTERNS:                                        │
│                                                             │
│  ❌ .venv/bin/python  (hard-coded path)                     │
│  ❌ /usr/bin/python3  (system-specific)                     │
│  ❌ python3.11        (version-specific)                    │
│                                                             │
│  REQUIRED PATTERNS:                                         │
│                                                             │
│  ✅ sys.executable    (in Python code)                      │
│  ✅ python -m module  (for CLI invocation)                  │
│  ✅ $(which python)   (in shell, if needed)                 │
│                                                             │
│  For tool dependencies (rg, uv, etc.):                      │
│  - Document in Prerequisites section                        │
│  - Add existence check in verification commands             │
│  - Provide installation instructions                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites (Verify Before Starting)

**ALL must pass before Phase 0 begins:**

- [ ] **Environment ready**: [verification command]
- [ ] **Dependencies installed**: [verification command]
- [ ] **Tests run successfully**: [verification command]
- [ ] **No blocking issues**: [verification command]
- [ ] **Required tools available**: [list tools with `which` checks]

**Quick Check**:
```bash
# Single command to verify all prerequisites
[PREREQ_CHECK_COMMAND]

# Tool availability (customize per project)
which python && which pytest && which rg || echo "Missing tools"
```

---

# Phase 0: Setup & Infrastructure

**Goal**: Establish testing infrastructure and baseline
**Time Estimate**: [X-Y hours]
**Status**: ⏳ NOT STARTED

---

## Task 0.1: [Task Name]

**Objective**: [One sentence]
**Files**: `[file1.py]`, `[file2.py]`

### TDD Step 1: Write Test First

```python
# tests/test_[name].py
def test_[feature]():
    """[What this test verifies]"""
    # Arrange
    [setup]
    
    # Act
    result = [function_call]
    
    # Assert - MUST be specific, not "it runs"
    assert result == [expected_specific_value]
    assert len(result.items) >= [minimum_expected]
    # Add assertions that would FAIL with stub implementation
```

```bash
# Verify test fails (RED)
[TEST_COMMAND]
# Expected: FAIL (test exists but implementation missing)
```

### ⛔ Test Strength Self-Check

Before proceeding to implementation:
- [ ] Would this test pass with `return None`? → If yes, strengthen it
- [ ] Does test verify specific output content? → Must be yes
- [ ] Does test have minimum count/value assertions? → Must be yes

### TDD Step 2: Implement

```python
# [file.py]
def [function]():
    """[Docstring]"""
    [implementation]
```

### TDD Step 3: Verify (GREEN)

```bash
# Run the specific test
[TEST_COMMAND]
# Expected: PASS

# Run full suite (no regressions)
[FULL_TEST_COMMAND]
# Expected: N/N PASS
```

### ⛔ STOP: Clean Table Check

Before marking this task complete, verify:

- [ ] Test passes (not skipped)
- [ ] **Test is strong** (fails with stub implementation)
- [ ] Full test suite passes: `[FULL_TEST_COMMAND]` → N/N PASS
- [ ] No TODOs or placeholders in new code
- [ ] No new warnings introduced
- [ ] Code is documented
- [ ] **All files in "Files:" header exist**: `test -f [each_file]`

**Status**: ⏳ NOT STARTED

---

## Task 0.2: [Next Task]

[Same structure as Task 0.1]

---

## ⛔ STOP: Phase 0 Gate

**Before starting Phase 1, ALL must be true:**

```bash
# 1. All tests pass
[FULL_TEST_COMMAND]
# Expected: N/N PASS

# 2. No regressions
[REGRESSION_CHECK]
# Expected: 0 failures

# 3. Clean Table verified
grep -r "TODO\|FIXME\|XXX" src/
# Expected: No results (or only pre-existing)

# 4. File manifest verified
for f in [ALL_PHASE_0_FILES]; do test -f "$f" || echo "MISSING: $f"; done
# Expected: No output (all files exist)
```

### Phase 0 Completion Checklist

- [ ] All Task 0.x items have ✅ status
- [ ] Full test suite passes
- [ ] **All tests are strong** (not "it runs" tests)
- [ ] No new TODOs introduced
- [ ] Infrastructure documented
- [ ] **All listed files exist**
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
# Only run this after ALL above criteria pass
# NOTE: Replace placeholders with ACTUAL values before running

PHASE_NUM=0
PHASE_NAME="Setup & Infrastructure"
TESTS_PASSED=$(pytest --collect-only -q 2>/dev/null | tail -1 | grep -oP '\d+(?= test)')
GIT_COMMIT=$(git rev-parse --short HEAD)
COMPLETION_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > .phase-${PHASE_NUM}.complete.json << EOF
{
  "schema_version": "1.0",
  "phase": ${PHASE_NUM},
  "phase_name": "${PHASE_NAME}",
  "tests_passed": ${TESTS_PASSED:-0},
  "tests_total": ${TESTS_PASSED:-0},
  "clean_table": true,
  "git_commit": "${GIT_COMMIT}",
  "completion_date": "${COMPLETION_DATE}"
}
EOF

# Verify no placeholders remain
grep -E "YYYY|placeholder|\[.*\]" .phase-${PHASE_NUM}.complete.json && \
    echo "❌ ERROR: Placeholders found in artifact" && exit 1

git add .phase-${PHASE_NUM}.complete.json
git commit -m "Phase ${PHASE_NUM} complete: ${PHASE_NAME}"
git tag phase-${PHASE_NUM}-complete
```

**Phase 0 Status**: ⏳ NOT STARTED

---

# Phase 1: [Phase Name]

**Goal**: [One sentence]
**Time Estimate**: [X-Y hours]
**Prerequisite**: `.phase-0.complete.json` must exist
**Status**: 📋 PLANNED

---

## ⛔ STOP: Verify Phase 0 Complete

```bash
# This MUST pass before starting Phase 1
test -f .phase-0.complete.json && echo "✅ Phase 0 complete" || echo "❌ BLOCKED"
```

---

## Task 1.1: [Task Name]

**Objective**: [One sentence]
**Files**: `[files]`

### TDD Step 1: Write Test First

[Test code with verification command]

**⛔ Test Strength Self-Check** (mandatory):
- [ ] Test fails with stub implementation
- [ ] Test verifies specific output values
- [ ] Test has boundary/count assertions

### TDD Step 2: Implement

[Implementation guidance]

### TDD Step 3: Verify

```bash
[TEST_COMMAND]
# Expected: PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Test passes
- [ ] **Test is strong**
- [ ] Full suite passes
- [ ] No new debt
- [ ] **All "Files:" exist**

**Status**: 📋 PLANNED

---

## Task 1.2: [Next Task]

[Same structure]

---

## ⛔ STOP: Phase 1 Gate

[Same structure as Phase 0 Gate, including file manifest verification]

---

# Appendix A: Rollback Procedures

## A.1: Single Test Failure

```bash
# 1. Identify failing test
[TEST_COMMAND] 2>&1 | head -50

# 2. If fixable in <15 min, fix it
# 3. If not fixable, revert last change
git diff HEAD~1 --stat
git checkout HEAD~1 -- [affected_file]

# 4. Verify tests pass again
[FULL_TEST_COMMAND]
```

## A.2: Multiple Test Failures (Full Revert)

```bash
# 1. Identify last known good state
git log --oneline -10

# 2. Hard reset to good commit
git reset --hard [GOOD_COMMIT]

# 3. Verify
[FULL_TEST_COMMAND]

# 4. Document what went wrong
echo "[DATE]: Reverted due to [REASON]" >> ISSUES.md
```

## A.3: Phase Gate Failure

```bash
# DO NOT proceed to next phase
# 1. Identify which criterion failed
# 2. Fix the specific issue
# 3. Re-run phase gate verification
# 4. Only proceed when ALL criteria pass
```

## A.4: Weak Test Discovered

```bash
# If a test is discovered to be an "it runs" test:
# 1. DO NOT proceed with current task
# 2. Strengthen the test first
# 3. Verify strengthened test fails with stub
# 4. Only then continue implementation
```

---

# Appendix B: AI Assistant Instructions

## Drift Prevention Rules

1. **Before each response**, re-read the current task's objective
2. **After completing code**, immediately run verification commands
3. **If test fails**, fix it before moving on (no "we'll fix it later")
4. **If blocked**, document why and suggest rollback
5. **Never skip** Clean Table checks
6. **Never write** "it runs" tests (see Test Strength Rules)
7. **Never list** files that won't be created

## Verification Frequency

| Action | Verify Immediately |
|--------|-------------------|
| Create new file | File exists, syntax valid |
| Modify function | Related tests pass |
| Write test | **Test fails with stub** |
| Complete task | Full test suite + file manifest |
| Complete phase | Phase gate checklist |

## When to Stop and Escalate

- Test suite drops below 100% pass rate
- Performance degrades beyond threshold
- Clean Table criteria cannot be satisfied
- Phase gate blocked for >2 attempts
- **Test discovered to be "it runs" pattern**
- **File listed but not created**

## Prohibited Actions

- ❌ Starting Phase N+1 without Phase N artifact
- ❌ Marking task complete with failing tests
- ❌ Leaving TODOs in "completed" code
- ❌ Skipping Clean Table verification
- ❌ Proceeding after rollback without re-verification
- ❌ **Writing tests that only check exit code**
- ❌ **Writing tests that pass with stub implementation**
- ❌ **Listing files in "Files:" that aren't created**
- ❌ **Leaving literal placeholders in artifacts**
- ❌ **Using hard-coded Python paths** (use sys.executable)

---

# Appendix C: File Change Tracking

Track all file changes for audit trail:

| Phase.Task | File | Action | Verified |
|------------|------|--------|----------|
| 0.1 | `src/module.py` | CREATE | ⏳ |
| 0.1 | `tests/test_module.py` | CREATE | ⏳ |
| 1.1 | `src/module.py` | UPDATE | 📋 |

**File Manifest Audit**:
```bash
# After each phase, verify all tracked files exist
cat << 'EOF' | while read line; do
    file=$(echo "$line" | awk '{print $3}')
    test -f "$file" && echo "✅ $file" || echo "❌ $file"
done
[PASTE_TABLE_HERE]
EOF
```

---

# Appendix D: Progress Log

## Session Log

```
[YYYY-MM-DD HH:MM] Started Phase 0
[YYYY-MM-DD HH:MM] Task 0.1 complete - tests: 5/5 PASS (strong tests verified)
[YYYY-MM-DD HH:MM] Task 0.2 complete - tests: 8/8 PASS
[YYYY-MM-DD HH:MM] Phase 0 Gate: ✅ ALL PASS
[YYYY-MM-DD HH:MM] File manifest: ✅ ALL FILES EXIST
[YYYY-MM-DD HH:MM] Created .phase-0.complete.json (no placeholders)
```

## Time Tracking

| Phase | Task | Estimated | Actual | Notes |
|-------|------|-----------|--------|-------|
| 0 | 0.1 | 1h | - | - |
| 0 | 0.2 | 2h | - | - |

---

# Appendix E: Test Strength Audit

Run this audit after writing tests to catch weak patterns:

```bash
# Find potential "it runs" tests
grep -rn "returncode == 0" tests/ | grep -v "# verified strong"
grep -rn "returncode in" tests/
grep -rn "assert.*in.*output" tests/ | grep -v "specific"

# Find tests without assertions
grep -l "def test_" tests/*.py | xargs -I{} sh -c \
    'grep -A20 "def test_" {} | grep -c "assert" | grep "^0$" && echo "Weak test in {}"'
```

If any weak patterns found, strengthen before proceeding.

---

# Template Customization Checklist

Before using this template, replace:

- [ ] `[PROJECT_NAME]` → Your project name
- [ ] `[FAST_TEST_COMMAND]` → e.g., `pytest tests/ -x -q`
- [ ] `[FULL_TEST_COMMAND]` → e.g., `pytest tests/ -v`
- [ ] `[PERF_TEST_COMMAND]` → e.g., `python benchmark.py`
- [ ] `[TEST_COMMAND]` → e.g., `pytest tests/test_specific.py -v`
- [ ] Phase names and task breakdowns
- [ ] Success criteria for your project
- [ ] **All "Files:" headers with actual files**
- [ ] **Tool dependencies in Prerequisites**

**Final verification**: `grep -E "\[.*\]" PROJECT_TASKS.md` should return only intentional placeholders.

---

**End of Template**
