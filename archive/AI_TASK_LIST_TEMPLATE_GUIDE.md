# AI_TASK_LIST_TEMPLATE - Usage Guide

**Version**: 1.0

---

## What This Template Solves

| Problem | Solution in Template |
|---------|---------------------|
| AI drifts from task | ⛔ STOP checkpoints force re-verification |
| Tasks marked "done" but aren't | Clean Table gates block progress |
| Tests written as afterthought | TDD protocol: test first, always |
| Phase N+1 starts before N is stable | Phase unlock artifacts required |
| "I'll fix it later" debt | No proceeding with failing tests |

---

## Core Concepts

### 1. STOP Checkpoints

Every task ends with:
```markdown
### ⛔ STOP: Clean Table Check
- [ ] Test passes
- [ ] Full suite passes
- [ ] No new debt
```

**Rule**: AI must verify ALL boxes before moving on.

### 2. Phase Gates

```
Phase 0 ──► .phase-0.complete.json ──► Phase 1 ──► ...
```

Cannot start Phase N+1 until:
- All Phase N tasks complete
- Phase N tests pass
- Clean Table verified
- `.phase-N.complete.json` artifact created

### 3. TDD Protocol (Every Task)

```
1. Write test (RED)    ← Test fails because code doesn't exist
2. Implement (GREEN)   ← Minimal code to pass
3. Verify (CLEAN)      ← Full suite, no regressions
```

### 4. Clean Table Definition

A task is **NOT COMPLETE** if any of these exist:
- Failing tests
- TODOs/FIXMEs in new code
- Unverified assumptions
- "We'll fix it later" items

---

## Quick Start

### Step 1: Copy Template

```bash
cp AI_TASK_LIST_TEMPLATE.md PROJECT_TASKS.md
```

### Step 2: Fill Project-Specific Values

Required replacements:
- `[PROJECT_NAME]` → Your project
- `[FAST_TEST_COMMAND]` → e.g., `pytest -x -q`
- `[FULL_TEST_COMMAND]` → e.g., `pytest -v`
- Phase/task breakdown for your work

### Step 3: Work Sequentially

```
Task 0.1 → Clean Table → Task 0.2 → Clean Table → Phase 0 Gate → Phase 1...
```

---

## For AI Assistants: Execution Rules

### Before Starting Any Task

1. Read task objective
2. Identify test command
3. Verify prerequisites pass

### After Completing Any Code

1. Run specified test immediately
2. Check for warnings/errors
3. Run full suite
4. Verify Clean Table

### When Tests Fail

```
IF fixable in <15 minutes:
    Fix it now
ELSE:
    Rollback (see Appendix A)
    Document in ISSUES.md
    Re-attempt with different approach
```

### Prohibited Shortcuts

- ❌ "Tests are probably fine" (run them)
- ❌ "I'll add tests later" (TDD means now)
- ❌ "This TODO is minor" (no TODOs in "done" code)
- ❌ "Phase gate is just ceremony" (it's enforcement)

---

## Verification Commands (Customize Per Project)

```bash
# Fast check (after each change)
pytest tests/test_current.py -x -q

# Full validation (before task completion)
pytest tests/ -v --tb=short

# Clean Table check
grep -rn "TODO\|FIXME\|XXX" src/
# Expected: no new results

# Phase gate
test -f .phase-N.complete.json && echo "OK" || echo "BLOCKED"
```

---

## When Things Go Wrong

### Test Failure
→ Fix immediately or rollback

### Phase Gate Blocked
→ Do NOT proceed; resolve failing criterion

### Multiple Failures
→ Full revert to last known good commit

### Lost Progress
→ Check `git reflog` for recovery

---

## Template Structure Summary

```
PROJECT_TASKS.md
├── Quick Status Dashboard      ← Current state at a glance
├── Success Criteria            ← Project-level "done"
├── Phase Gate Rules            ← Enforcement mechanism
├── TDD Protocol                ← Every task follows this
├── Clean Table Definition      ← What "complete" means
├── Prerequisites               ← Before Phase 0
│
├── Phase 0                     ← Setup & Infrastructure
│   ├── Task 0.1               ← TDD structure
│   │   ├── Write Test
│   │   ├── Implement
│   │   ├── Verify
│   │   └── ⛔ STOP: Clean Table
│   ├── Task 0.2
│   └── ⛔ STOP: Phase 0 Gate
│
├── Phase 1...N                 ← Same structure
│
├── Appendix A: Rollback        ← When things fail
├── Appendix B: AI Instructions ← Behavioral rules
├── Appendix C: File Tracking   ← Audit trail
└── Appendix D: Progress Log    ← Time/session tracking
```

---

## Key Differences from Original Templates

| Original | Combined Template |
|----------|------------------|
| Many placeholders (`{{VAR}}`) | Fewer, clearer placeholders |
| Phase unlock optional | Phase unlock **required** |
| Clean Table suggested | Clean Table **enforced** |
| TDD mentioned | TDD **structured into every task** |
| Complex evidence system | Simplified to essential tracking |
| Separate formats | Single unified format |

---

## Customization Points

**Must customize:**
- Test commands (project-specific)
- Phase/task breakdown
- Success criteria

**Can keep as-is:**
- STOP checkpoint structure
- Clean Table definition
- Rollback procedures
- AI instruction appendix

---

## Example: Minimal Project

```markdown
# MyFeature - Detailed Task List

**Project**: Add user authentication
**Status**: Phase 0 - NOT STARTED

## Success Criteria
- [ ] Login endpoint works
- [ ] Tests pass: `pytest tests/auth/ -v`
- [ ] No security warnings

## Phase 0: Setup

### Task 0.1: Create auth module skeleton

**TDD Step 1**: Write test
```python
def test_auth_module_exists():
    from myapp import auth
    assert hasattr(auth, 'login')
```

**TDD Step 2**: Implement
```python
# myapp/auth.py
def login(username, password):
    raise NotImplementedError
```

**TDD Step 3**: Verify
```bash
pytest tests/test_auth.py -v
# Expected: PASS (function exists)
```

### ⛔ STOP: Clean Table Check
- [ ] Test passes
- [ ] No TODOs

**Status**: ⏳ NOT STARTED
```

---

**End of Usage Guide**
