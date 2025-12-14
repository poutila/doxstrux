# AI_TASK_LIST_TEMPLATE - Usage Guide

**Version**: 2.0

---

## What This Template Solves

| Problem | Solution in Template |
|---------|---------------------|
| AI drifts from task | ⛔ STOP checkpoints force re-verification |
| Tasks marked "done" but aren't | Clean Table gates block progress |
| Tests written as afterthought | TDD protocol: test first, always |
| Phase N+1 starts before N is stable | Phase unlock artifacts required |
| "I'll fix it later" debt | No proceeding with failing tests |
| **"It runs" tests capture nothing** | **Test Strength Rules forbid weak tests** |
| **Files listed but never created** | **File Manifest verification** |
| **Placeholders committed to repo** | **Artifact generation uses shell variables** |
| **Hard-coded paths break portability** | **Environment Portability Rules** |
| **Later phases relax TDD** | **Every phase requires test skeletons** |

---

## Core Concepts

### 1. STOP Checkpoints

Every task ends with:
```markdown
### ⛔ STOP: Clean Table Check
- [ ] Test passes
- [ ] **Test is strong** (fails with stub)
- [ ] Full suite passes
- [ ] No new debt
- [ ] **All "Files:" exist**
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
- **File manifest verified**
- **No placeholders in artifact**

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
- **Files listed but not created**
- **Tests that pass with stub implementations**
- **Literal placeholders in committed files**

---

## NEW in v2.0: Anti-Drift Mechanisms

### 5. Test Strength Rules

**The core problem**: Tests like `assert returncode == 0` don't verify behavior. A stub implementation that does nothing passes these tests.

**The solution**: Every test must have assertions that would **fail** with a stub implementation.

```python
# ❌ FORBIDDEN - passes with empty implementation
def test_discover():
    result = subprocess.run(["python", "tools/discover.py"])
    assert result.returncode == 0

# ✅ REQUIRED - fails with empty implementation
def test_discover():
    result = subprocess.run(["python", "tools/discover.py"])
    assert result.returncode == 0
    
    # These assertions FAIL if tool does nothing:
    output = Path("output.txt")
    assert output.exists()
    lines = output.read_text().strip().split("\n")
    assert len(lines) >= 10  # Must produce real output
    assert "expected_key" in lines  # Must have specific content
```

**Self-check question**: "Would this test pass if `def my_function(): return None`?"
- If YES → Test is too weak, strengthen it
- If NO → Test is acceptable

### 6. File Manifest Verification

**The core problem**: Task headers list files that are never actually created ("ghost files"). This creates confusion and drift.

**The solution**: Every file listed in a task's `Files:` header must:
1. Have a creation/modification step in that task
2. Actually exist after task completion
3. Be verifiable via `test -f`

```bash
# After every task, run:
for f in [FILES_FROM_HEADER]; do
    test -f "$f" && echo "✅ $f" || echo "❌ MISSING: $f"
done
```

### 7. Placeholder Prevention

**The core problem**: Phase artifacts with literal `YYYY-MM-DD` or `[PLACEHOLDER]` get committed.

**The solution**: Artifact generation uses shell variables that expand at runtime:

```bash
# ❌ FORBIDDEN - creates literal placeholders
cat > .phase-0.complete.json << 'EOF'
{
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF

# ✅ REQUIRED - expands to real values
COMPLETION_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > .phase-0.complete.json << EOF
{
  "completion_date": "${COMPLETION_DATE}"
}
EOF

# Verify no placeholders remain
grep -E "YYYY|placeholder|\[.*\]" .phase-0.complete.json && exit 1
```

### 8. Environment Portability

**The core problem**: Hard-coded paths like `.venv/bin/python` break on different systems.

**The solution**: Use portable patterns:

| ❌ Forbidden | ✅ Required |
|-------------|------------|
| `.venv/bin/python` | `sys.executable` (in Python) |
| `/usr/bin/python3` | `python -m module` (CLI) |
| `python3.11` | `$(which python)` (shell) |

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
- **All `Files:` headers with real filenames**

### Step 3: Verify No Placeholders Remain

```bash
grep -E "\[.*\]" PROJECT_TASKS.md
# Should return only intentional placeholders (if any)
```

### Step 4: Work Sequentially

```
Task 0.1 → Clean Table → Task 0.2 → Clean Table → Phase 0 Gate → Phase 1...
```

---

## For AI Assistants: Execution Rules

### Before Starting Any Task

1. Read task objective
2. Identify test command
3. Verify prerequisites pass
4. **Note all files listed in `Files:` header**

### After Writing Any Test

1. **Run stub check**: Would test pass with `return None`?
2. If yes → Strengthen test before proceeding
3. If no → Proceed to implementation

### After Completing Any Code

1. Run specified test immediately
2. Check for warnings/errors
3. Run full suite
4. Verify Clean Table
5. **Verify all `Files:` exist**

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
- ❌ **"Exit code 0 means it works"** (test actual behavior)
- ❌ **"I'll create that file later"** (if listed, create now)
- ❌ **"The placeholder is obvious"** (no placeholders in artifacts)

---

## Test Strength Patterns

### Pattern 1: Output File Verification

```python
# ❌ Weak
assert Path("output.txt").exists()

# ✅ Strong
output = Path("output.txt")
assert output.exists()
content = output.read_text()
assert len(content) > 0
assert "expected_header" in content
lines = content.strip().split("\n")
assert len(lines) >= 5
```

### Pattern 2: Tool Invocation

```python
# ❌ Weak
result = run(["tool"])
assert result.returncode == 0

# ✅ Strong
result = run(["tool", "--input", "test.json"], capture_output=True)
assert result.returncode == 0
stdout = result.stdout.decode()
assert "processed: 10" in stdout  # Specific expected output
assert "errors: 0" in stdout
```

### Pattern 3: Validation Tools

```python
# ❌ Weak - accepts any outcome
result = run(["validate"])
assert result.returncode in (0, 1)

# ✅ Strong - tests both paths
def test_validator_accepts_valid():
    result = run(["validate", "valid.json"], capture_output=True)
    assert result.returncode == 0
    assert "PASS" in result.stdout.decode()

def test_validator_rejects_invalid():
    result = run(["validate", "invalid.json"], capture_output=True)
    assert result.returncode == 1
    assert "FAIL" in result.stdout.decode()
    assert "line 5" in result.stderr.decode()  # Specific error location
```

### Pattern 4: Data Processing

```python
# ❌ Weak
result = process(data)
assert result is not None

# ✅ Strong
result = process(data)
assert isinstance(result, list)
assert len(result) == 3
assert result[0]["key"] == "expected_value"
assert all("required_field" in item for item in result)
```

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

# Test strength audit
grep -rn "returncode == 0" tests/ | grep -v "# strong"
grep -rn "returncode in" tests/
# Expected: no results (or all marked as verified strong)

# File manifest check
for f in FILE1 FILE2 FILE3; do test -f "$f" || echo "MISSING: $f"; done

# Placeholder check
grep -E "YYYY|placeholder|\[.*\]" .phase-*.complete.json
# Expected: no results
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

### Weak Test Discovered
→ Stop current work, strengthen test, verify it fails with stub, then continue

### Ghost File Found
→ Either create the file or remove from `Files:` header

### Placeholder in Artifact
→ Regenerate artifact with proper shell variable expansion

---

## Template Structure Summary

```
PROJECT_TASKS.md
├── Quick Status Dashboard      ← Current state at a glance
├── Success Criteria            ← Project-level "done"
├── Phase Gate Rules            ← Enforcement mechanism
├── TDD Protocol                ← Every task follows this
├── Test Strength Rules         ← NEW: Forbids weak tests
├── Clean Table Definition      ← What "complete" means
├── File Manifest Rules         ← NEW: No ghost files
├── Environment Portability     ← NEW: No hard-coded paths
├── Prerequisites               ← Before Phase 0
│
├── Phase 0                     ← Setup & Infrastructure
│   ├── Task 0.1               ← TDD structure
│   │   ├── Write Test
│   │   ├── Test Strength Check ← NEW
│   │   ├── Implement
│   │   ├── Verify
│   │   └── ⛔ STOP: Clean Table
│   ├── Task 0.2
│   └── ⛔ STOP: Phase 0 Gate
│
├── Phase 1...N                 ← Same structure (ALL phases need tests)
│
├── Appendix A: Rollback        ← When things fail
├── Appendix B: AI Instructions ← Behavioral rules (updated)
├── Appendix C: File Tracking   ← Audit trail
├── Appendix D: Progress Log    ← Time/session tracking
└── Appendix E: Test Audit      ← NEW: Catch weak tests
```

---

## Key Differences from v1.0

| v1.0 | v2.0 |
|------|------|
| "It runs" tests allowed implicitly | Test Strength Rules forbid them |
| Files in header could be ghosts | File Manifest verification required |
| Placeholder artifacts possible | Shell variable expansion + verification |
| Hard-coded paths common | Environment Portability Rules |
| Later phases could be prose-only | All phases require test skeletons |
| 3 enforcement mechanisms | 5 enforcement mechanisms |

---

## Customization Points

**Must customize:**
- Test commands (project-specific)
- Phase/task breakdown
- Success criteria
- **All `Files:` headers**

**Can keep as-is:**
- STOP checkpoint structure
- Clean Table definition
- Test Strength Rules
- File Manifest Rules
- Rollback procedures
- AI instruction appendix

---

## Common Anti-Patterns to Avoid

### Anti-Pattern 1: The Ceremonial Test
```python
# Looks like a test but verifies nothing
def test_module_exists():
    import mymodule  # Passes even if module is empty
    assert True
```
**Fix**: Test actual behavior of the module.

### Anti-Pattern 2: The Optimistic Validator
```python
# Accepts both success and failure as "passing"
assert result.returncode in (0, 1)
```
**Fix**: Test success and failure paths separately.

### Anti-Pattern 3: The Ghost File
```markdown
**Files**: `tools/verify.py`, `tools/analyze.py`

### Implementation
[Only creates verify.py, analyze.py mentioned but never created]
```
**Fix**: Either create all listed files or remove from header.

### Anti-Pattern 4: The Immortal Placeholder
```json
{
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
```
**Fix**: Use shell variable expansion when generating artifacts.

### Anti-Pattern 5: The Prose Phase
```markdown
## Phase 4: Integration

### Task 4.1: Full Integration

Just run everything together and make sure it works.
Use your judgment to verify correctness.
```
**Fix**: Define concrete test skeletons with specific assertions.

---

## Checklist for AI Agents

Before marking ANY task complete:

```
□ Test exists and is written FIRST
□ Test FAILS with stub implementation (verified)
□ Implementation makes test pass
□ Full test suite passes
□ No TODOs/FIXMEs in new code
□ All files in "Files:" header exist
□ No warnings introduced
□ Code is production-ready

Before marking ANY phase complete:

□ All tasks complete (above checklist for each)
□ Phase gate verification passes
□ .phase-N.complete.json created
□ NO PLACEHOLDERS in artifact (verified with grep)
□ Git tag created
```

---

**End of Usage Guide**
