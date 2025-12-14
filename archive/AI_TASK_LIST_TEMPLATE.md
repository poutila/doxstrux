# AI_TASK_LIST_TEMPLATE.md

**Purpose**: Unified task execution template for AI assistants. Prevents drift, enforces completion, bakes in TDD and Clean Table.

**Version**: 1.0
**Based On**: DETAILED_TASK_LIST_template.md, NEXT_STEPS_FORMAT.md

---

## How This Template Works

This template has three enforcement mechanisms:

1. **STOP Checkpoints** — AI must pause and verify before continuing
2. **Phase Gates** — Cannot advance until all criteria pass
3. **Clean Table Rule** — No debt carries forward

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

2. IMPLEMENT minimum code to pass
   └── Test must pass (green)

3. VERIFY no regressions
   └── Run: [full_test_command]
   └── Expected: N/N PASS

4. CLEAN TABLE CHECK
   └── No TODOs, no placeholders, no warnings
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

## 🧹 Clean Table Definition

> A task is CLEAN only when ALL are true:

- ✅ No unresolved errors or warnings
- ✅ No TODOs, FIXMEs, or placeholders in changed code
- ✅ No unverified assumptions
- ✅ No duplicated or conflicting logic
- ✅ Tests pass (not skipped, not mocked away)
- ✅ Code is production-ready (not "good enough for now")

**If any box is unchecked → task is NOT complete.**

---

## Prerequisites (Verify Before Starting)

**ALL must pass before Phase 0 begins:**

- [ ] **Environment ready**: [verification command]
- [ ] **Dependencies installed**: [verification command]
- [ ] **Tests run successfully**: [verification command]
- [ ] **No blocking issues**: [verification command]

**Quick Check**:
```bash
# Single command to verify all prerequisites
[PREREQ_CHECK_COMMAND]
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
    
    # Assert
    assert result == [expected]
```

```bash
# Verify test fails (RED)
[TEST_COMMAND]
# Expected: FAIL (test exists but implementation missing)
```

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
- [ ] Full test suite passes: `[FULL_TEST_COMMAND]` → N/N PASS
- [ ] No TODOs or placeholders in new code
- [ ] No new warnings introduced
- [ ] Code is documented

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
```

### Phase 0 Completion Checklist

- [ ] All Task 0.x items have ✅ status
- [ ] Full test suite passes
- [ ] No new TODOs introduced
- [ ] Infrastructure documented
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
# Only run this after ALL above criteria pass
cat > .phase-0.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 0,
  "phase_name": "Setup & Infrastructure",
  "tests_passed": [N],
  "tests_total": [N],
  "clean_table": true,
  "git_commit": "[COMMIT_HASH]",
  "completion_date": "[ISO_TIMESTAMP]"
}
EOF

git add .phase-0.complete.json
git commit -m "Phase 0 complete: infrastructure ready"
git tag phase-0-complete
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

### TDD Step 2: Implement

[Implementation guidance]

### TDD Step 3: Verify

```bash
[TEST_COMMAND]
# Expected: PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Test passes
- [ ] Full suite passes
- [ ] No new debt

**Status**: 📋 PLANNED

---

## Task 1.2: [Next Task]

[Same structure]

---

## ⛔ STOP: Phase 1 Gate

[Same structure as Phase 0 Gate]

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

---

# Appendix B: AI Assistant Instructions

## Drift Prevention Rules

1. **Before each response**, re-read the current task's objective
2. **After completing code**, immediately run verification commands
3. **If test fails**, fix it before moving on (no "we'll fix it later")
4. **If blocked**, document why and suggest rollback
5. **Never skip** Clean Table checks

## Verification Frequency

| Action | Verify Immediately |
|--------|-------------------|
| Create new file | File exists, syntax valid |
| Modify function | Related tests pass |
| Complete task | Full test suite |
| Complete phase | Phase gate checklist |

## When to Stop and Escalate

- Test suite drops below 100% pass rate
- Performance degrades beyond threshold
- Clean Table criteria cannot be satisfied
- Phase gate blocked for >2 attempts

## Prohibited Actions

- ❌ Starting Phase N+1 without Phase N artifact
- ❌ Marking task complete with failing tests
- ❌ Leaving TODOs in "completed" code
- ❌ Skipping Clean Table verification
- ❌ Proceeding after rollback without re-verification

---

# Appendix C: File Change Tracking

Track all file changes for audit trail:

| Phase.Task | File | Action | Verified |
|------------|------|--------|----------|
| 0.1 | `src/module.py` | CREATE | ⏳ |
| 0.1 | `tests/test_module.py` | CREATE | ⏳ |
| 1.1 | `src/module.py` | UPDATE | 📋 |

---

# Appendix D: Progress Log

## Session Log

```
[YYYY-MM-DD HH:MM] Started Phase 0
[YYYY-MM-DD HH:MM] Task 0.1 complete - tests: 5/5 PASS
[YYYY-MM-DD HH:MM] Task 0.2 complete - tests: 8/8 PASS
[YYYY-MM-DD HH:MM] Phase 0 Gate: ✅ ALL PASS
[YYYY-MM-DD HH:MM] Created .phase-0.complete.json
```

## Time Tracking

| Phase | Task | Estimated | Actual | Notes |
|-------|------|-----------|--------|-------|
| 0 | 0.1 | 1h | - | - |
| 0 | 0.2 | 2h | - | - |

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

---

**End of Template**
