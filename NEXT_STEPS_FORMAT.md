# NEXT_STEPS_FORMAT.md

**Purpose**: Template for step-by-step execution plans with Clean Table enforcement.

---

## Format Overview

This format ensures:
1. **Verifiable progress** - Each step has immediate test commands
2. **Clean Table gates** - No moving forward with debt
3. **Clear success criteria** - Measurable outcomes
4. **Traceability** - What files change, why, and when

---

## Template Structure

```markdown
# [DOCUMENT_NAME].md - [Brief Description]

**Status**: [Phase X.Y - IN PROGRESS | COMPLETE | BLOCKED]
**Version**: [X.Y]
**Last Updated**: [YYYY-MM-DD HH:MM UTC]
**Last Verified**: [YYYY-MM-DD HH:MM UTC] ([test count], [runtime])

**Related Documents**:
- [DOC_1.md] - [purpose]
- [DOC_2.md] - [purpose]

---

## Current Status

### Quick Status Dashboard

| Phase | Status | Tests | Files Changed | Clean Table |
|-------|--------|-------|---------------|-------------|
| X.0 - [Name] | ✅ COMPLETE | N/N | M | ✅ PASS |
| X.1 - [Name] | ⏳ IN PROGRESS | - | - | - |
| X.2 - [Name] | 📋 PLANNED | - | - | - |

---

## Prerequisites

**ALL must be verified before starting**:

- [ ] **[Prereq 1]**: [Description]
  ```bash
  # Verification command
  ```
- [ ] **[Prereq 2]**: [Description]

**Quick Verification**:
```bash
[single command that verifies all prerequisites]
```

---

## Phase X.Y - [Phase Name]

**Goal**: [One sentence]
**Estimated Time**: [X-Y hours]
**Clean Table Required**: Yes

### Task X.Y.1: [Task Name]

- [ ] **[Sub-task A]**:
  ```python
  # Code example or pseudo-code
  ```

- [ ] **[Sub-task B]**

**Test Immediately**:
```bash
# Actual runnable commands
[command]
# Expected: [what success looks like]
```

**Clean Table Check**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] Existing tests still pass
- [ ] No TODOs or placeholders

---

### Task X.Y.2: [Next Task]

[Same structure as above]

---

### Phase X.Y Final Validation

**X.Y Success Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Test Commands**:
```bash
[command 1]
[command 2]
```

**Clean Table Check for Phase X.Y**:
- [ ] All success criteria met
- [ ] No warnings or errors
- [ ] Code is production-ready
- [ ] Documentation updated

---

## File Changes Summary

| File | Action | Phase |
|------|--------|-------|
| `path/to/file.py` | CREATE | X.Y |
| `path/to/other.py` | UPDATE | X.Y |
| `tests/test_x.py` | CREATE | X.Y |

---

## Success Criteria (Overall)

- [ ] [High-level criterion 1]
- [ ] [High-level criterion 2]
- [ ] All tests pass: `[test command]`
- [ ] Clean Table achieved

---

## Clean Table Principle

> A final answer is considered CLEAN only if ALL of the following are true:
> - ✅ No unresolved errors, warnings, TODOs, placeholders
> - ✅ No unverified assumptions
> - ✅ No duplicated or conflicting logic
> - ✅ Solution is canonical and production-ready
> - ✅ No workarounds masking symptoms

**Each checkbox must be fully complete before proceeding to next step.**

---

## What's Next

**After this document is complete**:
1. [Next action 1]
2. [Next action 2]

---

**End of [DOCUMENT_NAME].md**
```

---

## Key Principles

### 1. Immediate Verification

Every task has a "Test Immediately" block with **actual runnable commands**:

```markdown
**Test Immediately**:
```bash
uv run python -c "from module import func; print(func())"
# Expected: [specific output]
```
```

### 2. Clean Table Gates

After each task, verify cleanliness before proceeding:

```markdown
**Clean Table Check**:
- [ ] Task objective achieved
- [ ] Test produces expected output
- [ ] No TODOs or placeholders
- [ ] Existing tests still pass (N/N)
```

### 3. Measurable Success Criteria

Use quantifiable criteria:

```markdown
**Success Criteria**:
- [ ] Test suite: **N/N PASS** (100% pass rate)
- [ ] Performance: <X seconds
- [ ] Cost: <$X.XX per run
- [ ] Coverage: X% of entities
```

### 4. File Change Tracking

Always document what files are touched:

```markdown
| File | Action | Reason |
|------|--------|--------|
| `src/module.py` | UPDATE | Add new function |
| `tests/test_module.py` | CREATE | Test new function |
```

### 5. Phase Dependencies

Each phase must declare prerequisites:

```markdown
## Prerequisites (ALL VERIFIED)

- [x] **Phase X-1 complete**: All tests pass
- [x] **Imports working**: `uv run python -c "from pkg import x"`
- [x] **No blocking issues**: Zero TODOs in codebase
```

---

## Status Indicators

| Indicator | Meaning |
|-----------|---------|
| ✅ COMPLETE | Done and verified |
| ⏳ IN PROGRESS | Currently working |
| 📋 PLANNED | Not started |
| ❌ BLOCKED | Cannot proceed |
| ⚠️ DEFERRED | Intentionally postponed |

---

## Example: Minimal Task

```markdown
### Task 1.2: Add validation function

- [ ] Create `validate()` in `src/validator.py`
- [ ] Return `bool` indicating pass/fail

**Test Immediately**:
```bash
uv run python -c "from validator import validate; assert validate('test.py') == True"
# Expected: No assertion error
```

**Clean Table Check**:
- [ ] Function exists and returns bool
- [ ] Test passes
- [ ] No hardcoded paths
```

---

## When to Use This Format

**Use for**:
- Multi-phase implementation plans
- Features requiring multiple file changes
- Work that needs verification gates
- Collaborative work where progress must be trackable

**Don't use for**:
- Single-file bug fixes
- Trivial changes
- Research/exploration tasks

---

## Adaptation Notes

1. **Scale phases** to actual work size (2-4 hours per phase is ideal)
2. **Test commands must be copy-pasteable** - no placeholders
3. **Success criteria must be objective** - "works correctly" is not measurable
4. **Clean Table checks are non-negotiable** - skip nothing
